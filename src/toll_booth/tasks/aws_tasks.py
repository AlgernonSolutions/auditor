import boto3
import rapidjson
from botocore.exceptions import ClientError
from algernon import ajson


def check_for_archived_encounter(bucket_name, id_source, client_id, encounter_id):
    file_key = f'{id_source}/{client_id}/{encounter_id}'
    try:
        stored_encounter = boto3.resource('s3').Object(bucket_name, file_key)
        encounter_response = stored_encounter.get()
        encounter = encounter_response['Body'].read()
        return rapidjson.loads(encounter)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None
        raise e


def publish_to_incredible(bullhorn,
                          flow_id,
                          id_source,
                          patient_id,
                          provider_id,
                          encounter_id,
                          encounter_datetime_in,
                          encounter_datetime_out,
                          encounter_type,
                          patient_last_name,
                          patient_first_name,
                          patient_dob):
    next_task_name = 'get_encounter'
    encounter_data = {
        'encounter_id': encounter_id,
        'encounter_datetime_in': encounter_datetime_in,
        'encounter_datetime_out': encounter_datetime_out,
        'patient_id': patient_id,
        'provider_id': provider_id,
        'encounter_type': encounter_type,
        'id_source':  id_source,
        'patient_last_name': patient_last_name,
        'patient_first_name': patient_first_name,
        'patient_dob': patient_dob
    }
    message = {
        'task_name': next_task_name,
        'task_kwargs': encounter_data,
        'flow_id': f'{flow_id}#{patient_id}#{next_task_name}-{encounter_id}'
    }
    listener_arn = bullhorn.find_task_arn('credible_tasks')
    strung_event = ajson.dumps(message)
    return bullhorn.publish('new_event', listener_arn, strung_event)


def publish_to_leech(bullhorn,
                     flow_id,
                     id_source,
                     patient_id,
                     provider_id,
                     encounter_id,
                     encounter_text,
                     encounter_datetime_in,
                     encounter_datetime_out,
                     encounter_type,
                     patient_last_name,
                     patient_first_name,
                     patient_dob):
    encounter_data = {
        'source': {
            'patient_id': patient_id,
            'provider_id': provider_id,
            'id_source': id_source,
            'encounter_id': encounter_id,
            'documentation': encounter_text,
            'encounter_datetime_in': encounter_datetime_in,
            'encounter_datetime_out': encounter_datetime_out,
            'encounter_type': encounter_type
        },
        'patient_data': [{
            'last_name': patient_last_name,
            'first_name': patient_first_name,
            'dob': patient_dob
        }]
    }
    message = {
        'task_name': 'leech',
        'task_kwargs': {
            'object_type': 'Encounter',
            'extracted_data': encounter_data
        },
        'flow_id': f'{flow_id}#leech'
    }
    listener_arn = bullhorn.find_task_arn('leech')
    strung_event = ajson.dumps(message)
    return bullhorn.publish('new_event', listener_arn, strung_event)
