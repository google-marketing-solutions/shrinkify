# Triggered every time a results table is created in the Shrinkify dataset.
# This Cloud Function takes the rows from the created result table that triggered it
# and appends it's rows in a unified final results table named "shrinkify_final"

import functions_framework
from google.cloud import bigquery

_OUTPUT_TABLE = 'shrinkify_final'

@functions_framework.cloud_event
def append_results(cloudevent):
    resource_name = log_and_get_resource(cloudevent)
    client = bigquery.Client()
    project = client.project

    dataset_id = resource_name.split('/')[3]
    source_table_id = resource_name.split('/')[-1]

    source_table = f"{project}.{dataset_id}.{source_table_id}"
    output_table = f"{project}.{dataset_id}.{_OUTPUT_TABLE}"

    # Create a job configuration to append data
    job_config = bigquery.QueryJobConfig(destination=output_table)
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

        # Create a query to append data
    query = f"SELECT *, TRIM(STRING(predictions[0].content)) AS short_title FROM `{source_table}`"
    append_job = client.query(query, job_config=job_config)

    # Wait for the job to complete
    append_job.result()


def log_and_get_resource(cloudevent):
    # Log function and trigger information
    print(f"Event type: {cloudevent['type']}")
    if 'subject' in cloudevent:
        print(f"Subject: {cloudevent['subject']}")
    
    payload = cloudevent.data.get("protoPayload")
    
    try:
        rows = int(payload['metadata']['tableDataChange']['insertedRowsCount'])
    except:
        print("Idle trigger.")
        return 0
    
    resource_name = payload.get('resourceName')
    print(f"Number of rows: {rows}")
    print(f"API method: {payload.get('methodName')}")
    print(f"Resource name: {resource_name}")
    print(f"Principal: {payload.get('authenticationInfo', dict()).get('principalEmail')}")
    return resource_name