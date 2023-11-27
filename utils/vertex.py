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
    