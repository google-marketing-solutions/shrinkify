import pandas as pd
import json
from utils.config import Config
from utils.bq import BigQueryInteractor
from utils.vertex import VertexBatchPredictionHandler

_MAX_ROW_PER_SUB_TABLE = 30000
_SHORT_TITLE_LENGTH = 28
_SUB_TABLE_PREFIX = 'sub_table_'
_SUB_RESULTS_TABLE_PREFIX = 'results_'

def create_prompt_base(config):
    examples = json.loads(config.examples_df.to_json(orient='records'))
    
    prompt = f"""You are a leading digital marketer working for a top {config.industry} company. You are an expert at generating high-performing short search ad titles ensuring that the ad titles only contain the important {config.product_type} information while keeping the title as short as possible and always less than  {_SHORT_TITLE_LENGTH} characters long. A user needs your help to shorten these {config.product_type} titles. Generate Short Title using the given "Context".
When you're done, check the length of the suggested {config.product_type} title, and if it's longer than {_SHORT_TITLE_LENGTH} characters try to make it even shorter by removing more words.
"""
    for example in examples:
            short_title = example.pop('Short Title')
            # example.pop('Character Count')
            prompt += f"""
Context:
{str(example)}
Short Title: {short_title}
"""
    
    return prompt


def create_prediction_sub_tables(config, bq):
    """Split the main feed to sub tables in BQ, each holding
    up to 30k rows, and holding the prompt for the predictions"""
    feed_row_count = bq.get_table_row_count(config.source_dataset, config.source_table)
    config.num_sub_tables = int(feed_row_count / _MAX_ROW_PER_SUB_TABLE) + 1
    prompt_base = create_prompt_base(config)

    for sub_table in range(config.num_sub_tables):
        table_name = _SUB_TABLE_PREFIX + str(sub_table)
        start_index = sub_table * _MAX_ROW_PER_SUB_TABLE
        end_index = (sub_table + 1) * _MAX_ROW_PER_SUB_TABLE - 1
        bq.extract_and_save_to_new_table(prompt_base, config.source_dataset, config.source_table,
                                         config.output_dataset, table_name, config.columns, start_index, end_index)


def init_bulk_predictions(config, bq):
    # TODO: b/313370000
    project_id = bq.get_project_id()
    source_dataset = config.source_dataset
    output_dataset = config.output_dataset
    num_sub_tables = config.num_sub_tables

    for i in range(num_sub_tables):
        print('start prediction ' + str(i))
        dataset = f'bq://{project_id}.{source_dataset}.{_SUB_TABLE_PREFIX}{i}'
        destination_uri_prefix = f'bq://{project_id}.{output_dataset}.{_SUB_RESULTS_TABLE_PREFIX}{i}'
        batch_predictions = VertexBatchPredictionHandler(dataset, destination_uri_prefix)
        batch_predictions.init_batch_prediction()
        print('start prediction ' + str(i))


def run(config_params): 
    config = Config.from_dict(config_params)
    bq = BigQueryInteractor()

    # Create shrinkify dataset
    bq.create_dataset(config.output_dataset)
    
    create_prediction_sub_tables(config, bq)
    init_bulk_predictions(config, bq)


# For testing purposes: 
# if __name__ == "__main__":
#     # Define the column names
#     columns = ["name", "country_id", "city_name", "address", "accommodation_type"]

#     json_file_path = './examples.json'

#     # Read the JSON file into a DataFrame
#     df = pd.read_json(json_file_path)

#     conf_dict = {'industry': 'Hotel Booking ',
#                 'product_type': 'Hotel',
#                 'source_dataset': 'batch_test',
#                 'source_table': 'Test Feed',
#                 'columns': columns,
#                 'examples_df': df}
#     run(conf_dict)