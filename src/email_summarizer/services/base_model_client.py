import json

from email_summarizer.services.bedrock_client import BedrockClient

class BaseModelClient:
  bedrock_client: BedrockClient
  model_id: str

  def __init__(self, bedrock_client: BedrockClient, model_id: str):
    self.bedrock_client = bedrock_client
    self.model_id = model_id

  def invoke(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500):
    # Request body
    body = json.dumps({
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    })
    # Send request
    response = self.bedrock_client.invoke_model(
      modelId=self.deepseek_inference_profile,
      body=body
    )
    # Read response
    return json.loads(response['body'].read())
