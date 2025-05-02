from unittest.mock import MagicMock, patch

import pytest
import json

from email_summarizer.services.bedrock_client import BedrockClient
from email_summarizer.services.nova_client import NovaClient, NovaClientFactory


class TestNovaClient:
    @pytest.fixture
    def bedrock_client(self):
        return MagicMock(spec=BedrockClient)

    @pytest.fixture
    def nova_client(self, bedrock_client):
        return NovaClient(
            bedrock_client=bedrock_client,
            model_id="test-model",
            temperature=0.4,
            max_tokens=1000,
        )

    def test_build_request_body(self, nova_client):
        prompt = "Test prompt"
        system_prompt = "Test system prompt"

        request_body = nova_client._build_request_body(prompt, system_prompt)

        assert request_body["schemaVersion"] == "messages-v1"
        assert request_body["messages"][0]["role"] == "user"
        assert request_body["messages"][0]["content"][0]["text"] == prompt
        assert request_body["system"][0]["text"] == system_prompt
        assert request_body["inferenceConfig"]["maxTokens"] == 1000
        assert request_body["inferenceConfig"]["temperature"] == 0.4
        assert request_body["inferenceConfig"]["topP"] == 0.7
        assert request_body["inferenceConfig"]["topK"] == 20

    def test_build_request_body_no_system_prompt(self, nova_client):
        prompt = "Test prompt"

        request_body = nova_client._build_request_body(prompt, None)

        assert request_body["system"][0]["text"] == ""

    def test_parse_response(self, nova_client):
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps(
            {"output": {"message": {"content": [{"text": "Test response"}]}}}
        ).encode()

        response = nova_client._parse_response(mock_response)

        assert response.response == "Test response"

    def test_parse_response_empty_content(self, nova_client):
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps(
            {"output": {"message": {"content": []}}}
        ).encode()

        with pytest.raises(ValueError, match="Empty content found in Nova response"):
            nova_client._parse_response(mock_response)

    def test_parse_response_missing_content(self, nova_client):
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps(
            {"output": {"message": {}}}
        ).encode()

        with pytest.raises(ValueError):
            nova_client._parse_response(mock_response)


class TestNovaClientFactory:
    @pytest.fixture
    def bedrock_client(self):
        return MagicMock(spec=BedrockClient)

    @pytest.fixture
    def factory(self):
        return NovaClientFactory()

    @patch.dict("os.environ", {"NOVA_INFERENCE_PROFILE": "test-profile"})
    def test_get_client_creates_new_client(self, factory, bedrock_client):
        client = factory.get_client(bedrock_client)

        assert isinstance(client, NovaClient)
        assert client.model_id == "test-profile"
        assert client.temperature == 0.4
        assert client.max_tokens == 1000

    @patch.dict("os.environ", {"NOVA_INFERENCE_PROFILE": "test-profile"})
    def test_get_client_reuses_existing_client(self, factory, bedrock_client):
        client1 = factory.get_client(bedrock_client)
        client2 = factory.get_client(bedrock_client)

        assert client1 is client2
