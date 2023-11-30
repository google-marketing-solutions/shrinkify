# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from utils.config import Config
from utils.bq import BigQueryInteractor
from utils.vertex import VertexBatchPredictionHandler


_MAX_ROW_PER_SUB_TABLE = 25000
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
            try:
                example.pop('Character Count')
            except:
                pass
            prompt += f"""
Context:
{str(example)}
Short Title: {short_title}-=
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
        print(f'Created sub_table_{sub_table}')

def init_first_bulk_prediction_job(config, bq):
    # TODO: b/313370000
    project_id = bq.get_project_id()
    output_dataset = config.output_dataset
    
    print('start prediction ' + str(0))
    dataset = f'bq://{project_id}.{output_dataset}.{_SUB_TABLE_PREFIX}0'
    destination_uri_prefix = f'bq://{project_id}.{output_dataset}.{_SUB_RESULTS_TABLE_PREFIX}0'
    batch_predictions = VertexBatchPredictionHandler(dataset, destination_uri_prefix)
    batch_predictions.init_batch_prediction()


def run(config_params): 
    config = Config.from_dict(config_params)
    bq = BigQueryInteractor()

    # Create shrinkify dataset
    bq.create_dataset(config.output_dataset)
    
    create_prediction_sub_tables(config, bq)
    init_first_bulk_prediction_job(config, bq)
