import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

import boto3
from botocore.exceptions import ClientError

from dotenv import load_dotenv

load_dotenv()


def configure_logging() -> None:
    """Set up structured logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class BedrockReasoningClient:
    """
    Client for interacting with Claude's reasoning capabilities via Amazon Bedrock.
    
    This class encapsulates the logic for setting up a connection to Amazon Bedrock
    and invoking Claude 3.7 Sonnet with reasoning capabilities enabled.
    """
    
    def __init__(
        self, 
        region_name: str | None, 
        profile_name: str | None,
        default_model_id: str | None
    ):
        """
        Initialize the BedrockReasoningClient.
        
        Args:
            region_name: AWS region for the Bedrock client
            default_model_id: Default Claude model ID to use
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.region_name = region_name or os.getenv("AWS_REGION")
        self.profile_name = profile_name or "data_reply"
        self.default_model_id = default_model_id or os.getenv("SONNET_MODEL_ID")
        self.client = self._create_client()
    
    def _create_client(self) -> Any:
        """
        Create and return a configured Amazon Bedrock runtime client.
        
        Returns:
            Configured Bedrock runtime client
        
        Raises:
            Exception: If client creation fails
        """
        try:
            # Using default credentials from environment or AWS config
            session = boto3.Session(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=self.region_name,
            )
            return session.client("bedrock-runtime")
        except Exception as e:
            self.logger.error(f"Failed to create Bedrock client: {e}")
            raise
    
    def invoke_reasoning(
        self,
        prompt: str,
        reasoning_budget: int = 2000,
        model_id: Optional[str] = None,
        temperature: float = 1,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Invoke Claude with reasoning capability enabled.
        
        Args:
            prompt: User prompt to send to Claude
            reasoning_budget: Token budget for the reasoning step
            model_id: Bedrock model ID to override default
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Tuple containing (reasoning_text, response_text)
            
        Raises:
            ClientError: If the Bedrock API returns an error
            KeyError: If the response has an unexpected structure
            Exception: For any other unexpected errors
        """
        model_id = model_id or self.default_model_id
        
        conversation = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]

        reasoning_config = {
            "thinking": {
                "type": "enabled",
                "budget_tokens": reasoning_budget
            }
        }
        
        # Additional model parameters
        inference_config = {
            "temperature": temperature,
        }

        try:
            self.logger.info(f"Invoking model {model_id} with reasoning enabled")
            response = self.client.converse(
                modelId=model_id,
                messages=conversation,
                inferenceConfig=inference_config,
                additionalModelRequestFields=reasoning_config
            )

            content_blocks = response["output"]["message"]["content"]

            reasoning_text = None
            response_text = None

            for block in content_blocks:
                if "reasoningContent" in block:
                    reasoning_text = block["reasoningContent"]["reasoningText"]["text"]
                if "text" in block:
                    response_text = block["text"]

            return reasoning_text, response_text

        except ClientError as e:
            self.logger.error(f"Bedrock API error: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Unexpected response structure: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unknown error during model invocation: {e}")
            raise
    
    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about the currently configured model.
        
        Args:
            model_id: Optional model ID to check, uses default if None
            
        Returns:
            Dictionary with model information
        """
        model_id = model_id or self.default_model_id
        return {
            "model_id": model_id,
            "region": self.region_name,
            "provider": "Anthropic" if "anthropic" in model_id.lower() else "Unknown",
            "version": model_id.split("-")[-1] if "-" in model_id else "Unknown"
        }


def main() -> None:
    """Execute the Claude reasoning demonstration."""
    configure_logging()
    logger = logging.getLogger("claude_reasoning_demo")
    
    try:
        # Complex chess puzzle that benefits from reasoning
        chess_puzzle_prompt = """
        You're given a chess position with the following pieces:
        - White King on e1
        - White Rook on h1
        - White Pawns on a2, b2, c2, d2, f2, g2, h2
        - Black King on e8
        - Black Queen on d8
        - Black Rooks on a8 and f8
        - Black Bishops on c8 and g7
        - Black Knights on b8 and g8
        - Black Pawns on a7, b7, c7, d7, e7, f7, h7
        
        White has just moved pawn from e2 to e4. Find the best move for Black and explain your reasoning step by step.
        """
        
        logger.info("Initializing BedrockReasoningClient")
        client = BedrockReasoningClient(None, None, None)
        
        # Print info about the model we're using
        model_info = client.get_model_info()
        logger.info(f"Using model: {model_info['model_id']} in {model_info['region']}")
        
        # Invoke the model with our chess puzzle
        reasoning, response = client.invoke_reasoning(
            prompt=chess_puzzle_prompt,
            reasoning_budget=3000,  # Increased budget for the complex chess problem
        )
        
        if reasoning and response:
            print("\n===== CLAUDE'S REASONING PROCESS =====")
            print(reasoning)
            print("\n===== CLAUDE'S FINAL RESPONSE =====")
            print(response)
        else:
            logger.warning("Received incomplete response from Claude")
            
    except Exception as e:
        logger.error(f"Failed to run demonstration: {e}")


if __name__ == "__main__":
    main()
