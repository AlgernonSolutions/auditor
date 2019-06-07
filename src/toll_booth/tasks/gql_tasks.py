from decimal import Decimal

import rapidjson
from algernon.aws.gql import GqlNotary

_get_flow = """
    query getState($flow_id: String!, $token: String){
        listStateEntries(flow_id: $flow_id, nextToken: $token){
            items{
                state_id
                state_type
                state_timestamp
                state_properties{
                    property_name
                    property_value
                }
            }
            nextToken
        }
    }
"""

_get_encounter = """
    query get_encounter($identifier_stem: String! $encounter_id: String!){
        get_vertex(identifier_stem: $identifier_stem, sid_value: $encounter_id){
            internal_id
            id_value{
                property_value{
                    ... on LocalPropertyValue{
                        data_type
                        property_value
                    }
                }
            }
            vertex_properties{
                property_name
                property_value{
                    ... on LocalPropertyValue{
                        data_type
                        property_value
                    }
                    ... on StoredPropertyValue{
                        data_type
                        storage_uri
                    }
                }
            }
        }
    }
"""

_get_client_encounters = """
    query get_client_internal_id($identifier_stem: String!, $client_id: String! $token:ID){
        get_vertex(identifier_stem: $identifier_stem, sid_value: $client_id){
            internal_id
            connected_edges(edge_labels:["_received_"], token: $token){
                page_info{
                    more
                    token
                }
                edges{
                    inbound{
                        edge_label
                        from_vertex{
                            vertex_type
                            id_value{
                                property_value{
                                    ... on LocalPropertyValue{
                                        data_type
                                        property_value
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
"""


def check_encounter_id(id_source, encounter_id, gql_endpoint):
    identifier_stem = f'#vertex#Encounter#{{\"id_source\": \"{id_source}\"}}#'
    gql_client = GqlNotary(gql_endpoint)
    variables = {
        'identifier_stem': identifier_stem,
        'encounter_id': str(encounter_id)
    }
    results = gql_client.send(_get_encounter, variables)
    parsed_results = rapidjson.loads(results)
    query_data = parsed_results['data']['get_vertex']
    return query_data


def check_client_encounter_ids(id_source, client_id, gql_endpoint):
    encounter_ids = []
    identifier_stem = f'#vertex#Patient#{{\"id_source\": \"{id_source}\"}}#'
    gql_client = GqlNotary(gql_endpoint)
    variables = {
        'identifier_stem': identifier_stem,
        'client_id': str(client_id)
    }
    results = gql_client.send(_get_client_encounters, variables)
    parsed_results = rapidjson.loads(results)
    query_data = parsed_results['data']['get_vertex']
    if not query_data:
        return None, None
    edge_data = query_data['connected_edges']['edges']['inbound']
    internal_id = query_data['internal_id']
    for edge in edge_data:
        encounter_id_value = edge['from_vertex']['id_value']['property_value']
        encounter_id = encounter_id_value['property_value']
        data_type = encounter_id_value['data_type']
        if data_type == 'N':
            encounter_id = Decimal(encounter_id)
        encounter_ids.append(encounter_id)
    return internal_id, encounter_ids


def check_flow_logs(legacy_flow_id, state_gql_endpoint):
    results = set()
    gql_client = GqlNotary(state_gql_endpoint)
    states, token = _paginate_flow(legacy_flow_id, gql_client)
    while token:
        new_states, token = _paginate_flow(legacy_flow_id, gql_client, token)
        states.extend(new_states)
    complete_events = [x for x in states if x['state_type'] == 'EventCompleted']
    for complete_event in complete_events:
        for property_entry in complete_event['state_properties']:
            if property_entry['property_name'] == 'task_results':
                results.add(property_entry['property_value'])
    if len(results) > 1:
        raise RuntimeError(f'too many results for flow_id: {legacy_flow_id}')
    for result in results:
        return result


def _paginate_flow(flow_id, gql_client, token=None):
    variables = {'flow_id': flow_id}
    if flow_id:
        variables.update({'nextToken': token})
    response = gql_client.send(_get_flow, variables)
    results = rapidjson.loads(response)
    entry_data = results['data']['listStateEntries']
    items = entry_data.get('items', [])
    token = entry_data.get('nextToken')
    return items, token
