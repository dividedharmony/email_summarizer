import os

from email_summarizer.services.base_model_client import BaseModelClient
from email_summarizer.services.bedrock_client import BedrockClient

class DeepseekClient(BaseModelClient):
  @property
  def deepseek_inference_profile(self) -> str:
    return self.model_id


class DeepseekClientFactory:
  deepseek_client: DeepseekClient | None

  def __init__(self):
    self.deepseek_client = None

  def get_client(self, bedrock_client: BedrockClient):
    if self.deepseek_client is None:
      self.deepseek_client = DeepseekClient(
        bedrock_client=bedrock_client,
        model_id=os.environ.get("DEEPSEEK_INFERENCE_PROFILE"),
        temperature=0.7,
        max_tokens=700
      )
    return self.deepseek_client
