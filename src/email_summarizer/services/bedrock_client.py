from typing import Any

import os
import boto3


class BedrockClient():
  boto3_client: Any
  deepseek_inference_profile: str

  def __init__(
      self, 
      service_name: str, 
      region: str, 
      aws_access_key: str, 
      aws_secret_access_key: str,
      deepseek_inference_profile: str
  ):
    self.boto3_client = boto3.client(
      service_name=service_name,
      region_name=region,
      aws_access_key_id=aws_access_key,
      aws_secret_access_key=aws_secret_access_key
    )
    self.deepseek_inference_profile = deepseek_inference_profile

  def invoke_model(self, **kwargs):
    return self.boto3_client.invoke_model(**kwargs)


class BedrockClientFactory:
  # class variables
  service_name = 'bedrock-runtime'
  region = 'us-east-1'

  # instance variables
  bedrock_client: BedrockClient | None

  def __init__(self):
    self.bedrock_client = None

  def get_client(self):
    if self.bedrock_client is None:
      self.bedrock_client = BedrockClient(
        service_name=BedrockClientFactory.service_name,
        region=BedrockClientFactory.region,
        aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        deepseek_inference_profile=os.environ.get("DEEPSEEK_INFERENCE_PROFILE")
      )
    return self.bedrock_client
