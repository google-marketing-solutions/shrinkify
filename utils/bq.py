from google.cloud import bigquery
from google.cloud.exceptions import Conflict

class BigQueryInteractor:
    def __init__(self):
        self.client = bigquery.Client()

    def get_datasets(self):
        datasets = list(self.client.list_datasets())
        return [dataset.dataset_id for dataset in datasets]

    def get_tables(self, dataset_id):
        dataset = self.client.dataset(dataset_id)
        tables = list(self.client.list_tables(dataset))
        return [table.table_id for table in tables]

    def get_column_names(self, dataset_id, table_id):
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)
        return [field.name for field in table.schema]

    def run_query(self, sql_query):
        query_job = self.client.query(sql_query)
        return query_job.result()

    def get_table_row_count(self, dataset_id, table_id):
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)
        return table.num_rows

    def get_project_id(self):
        return self.client.project
    
    def create_dataset(self, dataset_id, location="us-central1"):
        dataset_ref = bigquery.DatasetReference(self.client.project, dataset_id)
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        try:
            created_dataset = self.client.create_dataset(dataset)
            return created_dataset
        except Conflict as e:
            return dataset_id
    
    def extract_and_save_to_new_table(
        self,
        prompt_base,
        source_dataset_id,
        source_table_id,
        output_dataset_id,
        output_table_id,
        columns_to_select,
        start_index,
        end_index
    ):
        
        # Create a reference to the source table
        source_table_ref = self.client.dataset(
            source_dataset_id).table(source_table_id)

        # Create a reference to the destination table
        output_table_ref = self.client.dataset(
            output_dataset_id).table(output_table_id)

        # Basic query to select columns
        selected_columns = ', '.join(columns_to_select)

        # Creating the dictionary-like string with "Context: " prefix
        dict_representation = "CONCAT('Context: {', " + ", ', ', ".join(
            [f"'{col}: ', CAST({col} AS STRING)" for col in columns_to_select]) + ", '}')"

        # Creating the prompt string
        prompt_string = f"CONCAT(\"\"\"{prompt_base}\"\"\", {dict_representation}, ' Short title: ')"

        # Complete query with row number
        query = f"""
        CREATE TABLE `{output_table_ref}` AS
        WITH NumberedRows AS (
            SELECT 
                *,
                ROW_NUMBER() OVER() as rownum
            FROM 
                `{source_table_ref}`
        )
        SELECT 
            {selected_columns},
            {dict_representation} AS column_values_dict,
            {prompt_string} AS prompt
        FROM 
            NumberedRows
        WHERE 
            rownum BETWEEN {start_index} AND {end_index}
        """

        # Create a query job to extract data from the source table
        query_job = self.client.query(query)
        print(query)
        # Write the query results to the destination table
        # job_config = bigquery.QueryJobConfig(destination=destination_table_ref)
        query_job.result()
