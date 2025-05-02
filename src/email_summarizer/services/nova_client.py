import json
import os
import typing

from email_summarizer.services.base_model_client import (
    AbastractModelResponse,
    BaseModelClient,
    BaseModelResponse,
)
from email_summarizer.services.bedrock_client import BedrockClient
from email_summarizer.utils.general_utils import safe_dig


class NovaClient(BaseModelClient):
    @property
    def nova_inference_profile(self) -> str:
        return self.model_id

    @typing.override
    def _build_request_body(self, prompt: str, system_prompt: str | None) -> dict:
        """
        Build the request body for the model.
        """
        system_list = [{"text": system_prompt or ""}]
        message_list = [{"role": "user", "content": [{"text": prompt}]}]
        inf_params = {
            "maxTokens": self.max_tokens,
            "topP": 0.7,
            "topK": 20,
            "temperature": self.temperature,
        }
        return {
            "schemaVersion": "messages-v1",
            "messages": message_list,
            "system": system_list,
            "inferenceConfig": inf_params,
        }

    @typing.override
    def _parse_response(self, response: dict) -> AbastractModelResponse:
        response_body = json.loads(response["body"].read())
        contents = (
            safe_dig(
                data=response_body,
                keys=["output", "message", "content"],
                error_on_missing=True,
            )
            or []
        )
        if len(contents) == 0:
            raise ValueError("Empty content found in Nova response")
        text_content = contents[0]["text"]
        return BaseModelResponse(response=text_content)


class NovaClientFactory:
    nova_client: NovaClient | None

    def __init__(self):
        self.nova_client = None

    def get_client(self, bedrock_client: BedrockClient):
        if self.nova_client is None:
            self.nova_client = NovaClient(
                bedrock_client=bedrock_client,
                model_id=os.environ.get("NOVA_INFERENCE_PROFILE"),
                temperature=0.4,
                max_tokens=1000,
            )
        return self.nova_client
