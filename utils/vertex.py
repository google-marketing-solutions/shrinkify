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

from vertexai.preview.language_models import TextGenerationModel

_TEXT_MODEL = TextGenerationModel.from_pretrained("text-bison")
_MODEL_PARAMETERS = {
    "maxOutputTokens": "8",
    "temperature": "0.2",
    "topP": "0.95",
    "topK": "40",
}


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
    