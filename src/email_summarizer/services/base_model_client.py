import json

from email_summarizer.services.bedrock_client import BedrockClient

class BaseModelClient:
  bedrock_client: BedrockClient
  model_id: str
  temperature: float
  max_tokens: int

  def __init__(
      self,
      bedrock_client: BedrockClient,
      model_id: str,
      temperature: float,
      max_tokens: int
    ):
    self.bedrock_client = bedrock_client
    self.model_id = model_id
    self.temperature = temperature
    self.max_tokens = max_tokens

  def invoke(self, prompt: str):
    # Request body
    body = json.dumps(self._build_request_body(prompt=prompt))
    # Send request
    response = self.bedrock_client.invoke_model(
      modelId=self.model_id,
      body=body
    )
    # Read response
    return json.loads(response['body'].read())

  def _build_request_body(self, prompt: str) -> dict:
    """
    Build the request body for the model.
    """
    return {
      "prompt": prompt,
      "temperature": self.temperature,
      "max_tokens": self.max_tokens
    }
