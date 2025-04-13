import os
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

def main():
  # Create a Bedrock Runtime client
  bedrock_client = boto3.client(
      service_name='bedrock-runtime',
      region_name='us-east-1',  # Or your desired AWS region
      aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
      aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),  
  )

  # Model ID for DeepSeek R1.  Make sure this is correct for your region.
  inference_profile = os.environ.get("DEEPSEEK_INFERENCE_PROFILE")

  # Construct the prompt.  DeepSeek models often work best with specific formatting.
  prompt = "Write a short story about a cat."

  # Request body
  body = json.dumps({
      "prompt": prompt,
      "temperature": 0.8,  # Adjust as needed
      "max_tokens": 500     # Adjust as needed
  })

  # Invoke the model
  response = bedrock_client.invoke_model(
      modelId=inference_profile,
      body=body
  )

  # Parse the response
  response_body = json.loads(response['body'].read())

  # Print the output
  print(response_body)

if __name__ == "__main__":
  main()
