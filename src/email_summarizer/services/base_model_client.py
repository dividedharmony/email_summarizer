import json
from abc import abstractmethod

from pydantic import BaseModel

from email_summarizer.services.bedrock_client import BedrockClient


class AbastractModelResponse(BaseModel):
    @abstractmethod
    def get_response(self) -> str:
        pass


class AbstractModelClient:
    @abstractmethod
    def invoke(
        self, prompt: str, system_prompt: str | None = None
    ) -> AbastractModelResponse:
        pass


class BaseModelResponse(AbastractModelResponse):
    response: str

    def get_response(self) -> str:
        return self.response


class BaseModelClient(AbstractModelClient):
    bedrock_client: BedrockClient
    model_id: str
    temperature: float
    max_tokens: int

    def __init__(
        self,
        bedrock_client: BedrockClient,
        model_id: str,
        temperature: float,
        max_tokens: int,
    ):
        self.bedrock_client = bedrock_client
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

    def invoke(
        self, prompt: str, system_prompt: str | None = None
    ) -> AbastractModelResponse:
        # Request body
        body = json.dumps(
            self._build_request_body(prompt=prompt, system_prompt=system_prompt)
        )
        # Send request
        response = self.bedrock_client.invoke_model(modelId=self.model_id, body=body)
        # Read response
        return self._parse_response(response)

    def _parse_response(self, response: dict) -> AbastractModelResponse:
        return BaseModelResponse(response=json.loads(response["body"].read()))

    def _build_request_body(self, prompt: str, system_prompt: str | None) -> dict:
        """
        Build the request body for the model.
        """
        request_body = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if system_prompt:
            request_body["system_prompt"] = system_prompt
        return request_body
