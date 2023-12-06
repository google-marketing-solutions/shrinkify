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


_OUTPUT_DATASET = 'shrinkify_output'
_OUTPUT_TABLE = 'shrinkify_final'

class Config:
    def __init__(self, industry, product_type, char_limit, source_dataset, source_table, columns, examples_df) -> None:
        self.industry = industry
        self.product_type = product_type
        self.char_limit = char_limit
        self.source_dataset = source_dataset
        self.source_table = source_table
        self.columns = columns
        self.examples_df = examples_df
        self.output_dataset = _OUTPUT_DATASET
        self.output_table = _OUTPUT_TABLE
        self._num_sub_tables = 0

    @property
    def num_sub_tables(self):
        return self._num_sub_tables
    
    @num_sub_tables.setter
    def num_sub_tables(self, value):
        if value < 0:
            raise ValueError("Sub tables number cannot be nagative.")
        self._num_sub_tables = value

    @classmethod
    def from_dict(cls, config_dict):
        return cls(
            config_dict.get('industry'),
            config_dict.get('product_type'),
            config_dict.get('char_limit'),
            config_dict.get('source_dataset'),
            config_dict.get('source_table'),
            config_dict.get('columns'),
            config_dict.get('examples_df'),
        )

    def to_dict(self):
        return {
            'industry': self.industry,
            'product_type': self.product_type,
            'char_limit': self.char_limit,
            'source_dataset': self.source_dataset,
            'source_table': self.source_table,
            'output_dataset': self.output_dataset,
            'output_table': self.output_table,
            'columns': self.columns,
            'examples_df': self.examples_df
        }