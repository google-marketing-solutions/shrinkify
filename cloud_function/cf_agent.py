# Triggered every time a results table is created in the Shrinkify dataset.
# This Cloud Function takes the rows from the created result table that triggered it
# and appends it's rows in a unified final results table named "shrinkify_final".
# This then deletes the triggering 'results' table and the sub_table that created it, 
# and creates a new batch prediction job for the next sub_table if one exists. 

import functions_framework
from google.cloud import bigquery
from vertexai.preview.language_models import TextGenerationModel

_TEXT_MODEL = TextGenerationModel.from_pretrained("text-bison")
_MODEL_PARAMETERS = {
    "maxOutputTokens": "8",
    "temperature": "0.2",
    "topP": "0.95",
    "topK": "40",
}

_SUB_TABLE_PREFIX = 'sub_table_'
_SUB_RESULTS_TABLE_PREFIX = 'results_'
_OUTPUT_TABLE = 'shrinkify_final'

@functions_framework.cloud_event
def cloud_agent(cloudevent):
    resource_name = log_and_get_resource(cloudevent)
    if not resource_name:
        print("Idle trigger.")
        return 0

    dataset_id = resource_name.split('/')[3]
    results_table_id = resource_name.split('/')[-1]
    current_table_index = int(results_table_id.split('results_')[1])
    sub_table_id = _SUB_TABLE_PREFIX + str(current_table_index)

    client = bigquery.Client()
    append_results(client, dataset_id, results_table_id)
    delete_finished_tables(client, dataset_id, results_table_id, sub_table_id)
    try:
        trigger_next_batch_prediction(client.project, dataset_id, current_table_index)
    except Exception as e:
        f'Did not trigger prediction for sub table {str(current_table_index + 1)}'


def trigger_next_batch_prediction(project_id, dataset_id, current_table_index):
    i = str(current_table_index + 1)
    print('start prediction ' + i)
    dataset = f'bq://{project_id}.{dataset_id}.{_SUB_TABLE_PREFIX}{i}'
    destination_uri_prefix = f'bq://{project_id}.{dataset_id}.{_SUB_RESULTS_TABLE_PREFIX}{i}'
    batch_predictions = VertexBatchPredictionHandler(dataset, destination_uri_prefix)
    batch_predictions.init_batch_prediction()


def delete_finished_tables(client, dataset_id, results_table_id, sub_table_id):
    """Deletes the triggering 'results' table and the 'sub_table' that created it"""

    results_table_ref = client.dataset(dataset_id).table(results_table_id)
    sub_table_ref = client.dataset(dataset_id).table(sub_table_id)

    try:
        # Use the delete_table method to delete the table.
        client.delete_table(results_table_ref)
        print(f"Table {results_table_ref} deleted.")

        # Use the delete_table method to delete the table.
        client.delete_table(sub_table_ref)
        print(f"Table {sub_table_ref} deleted.")

    except Exception as e:
        print(f"Error in deleting table: {e}")
    
    
def append_results(client, dataset_id, results_table_id):
    project = client.project
    source_table = f"{project}.{dataset_id}.{results_table_id}"
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
        return 0
    
    resource_name = payload.get('resourceName')
    print(f"Number of rows: {rows}")
    print(f"API method: {payload.get('methodName')}")
    print(f"Resource name: {resource_name}")
    print(f"Principal: {payload.get('authenticationInfo', dict()).get('principalEmail')}")
    return resource_name


class VertexBatchPredictionHandler():
    def __init__(self, dataset, destination_uri_prefix):
        self.text_model = _TEXT_MODEL
        self.dataset = dataset
        self.destination_uri_prefix = destination_uri_prefix
        self.model_parameters = _MODEL_PARAMETERS
    
    def init_batch_prediction(self):
        self.text_model.batch_predict(
            dataset=self.dataset,
            destination_uri_prefix=self.destination_uri_prefix,
            model_parameters=self.model_parameters
        )
    