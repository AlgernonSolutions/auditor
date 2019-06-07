from algernon.aws import Bullhorn
from toll_booth.tasks import gql_tasks, aws_tasks
import os


def _retrieve_soft_variable(variable_name: str, search_kwargs, default=None):
    if variable_name in search_kwargs:
        return search_kwargs[variable_name]
    os_variable = os.getenv(variable_name.upper(), None)
    if os_variable:
        return os_variable
    if default:
        return default
    return None


def _check_legacy_flows(flow_ids, state_gql_endpoint):
    results = set()
    for flow_id in flow_ids:
        flow_results = gql_tasks.check_flow_logs(flow_id, state_gql_endpoint)
        results.add(flow_results)
    if len(results) > 1:
        raise RuntimeError(f'received multiple results when checking legacy flow_ids: {flow_ids}')
    for result in results:
        return result


def audit_surgeon_graph(id_source, client_id, encounter_id, encounter_data, **kwargs):
    legacy_flow_ids = [
        f"leech-psi-201905291215#get_client_encounter_ids-{client_id}#get_encounter-{encounter_id}"
    ]
    bullhorn = Bullhorn.retrieve()
    gql_endpoint = _retrieve_soft_variable('graph_gql_endpoint', kwargs)
    state_gql_endpoint = _retrieve_soft_variable('state_gql_endpoint', kwargs)
    bucket_name = _retrieve_soft_variable('encounter_bucket', kwargs)
    encounter = gql_tasks.check_encounter_id(id_source, encounter_id, gql_endpoint)
    publish_kwargs = {
        'bullhorn': bullhorn,
        'flow_id': f'review_surgeon#{client_id}#{encounter_id}',
        'id_source': id_source,
        'patient_id': client_id,
        'provider_id': encounter_data['Staff ID'],
        'encounter_id': encounter_id,
        'encounter_datetime_in': encounter_data['Time In'],
        'encounter_datetime_out': encounter_data['Time Out'],
        'encounter_type': encounter_data['Visit Type'],
        'patient_last_name': encounter_data['Last Name'],
        'patient_first_name': encounter_data['First Name'],
        'patient_dob': encounter_data['DOB']
    }
    results = {
        'client_id': client_id,
        'encounter_id': encounter_id
    }
    if not encounter:
        encounter = aws_tasks.check_for_archived_encounter(bucket_name, id_source, client_id, encounter_id)
    if not encounter:
        encounter = _check_legacy_flows(legacy_flow_ids, state_gql_endpoint)
    if not encounter:
        publish_results = aws_tasks.publish_to_incredible(**publish_kwargs)
        results.update({'publish_results': publish_results, 'destination': 'get_encounter'})
        return results
    publish_kwargs.update({'encounter_text': encounter})
    publish_results = aws_tasks.publish_to_leech(**publish_kwargs)
    results.update({'publish_results': publish_results, 'destination': 'leech'})
    return results
