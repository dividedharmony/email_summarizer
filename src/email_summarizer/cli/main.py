from dotenv import load_dotenv
from email_summarizer.services.bedrock_client import BedrockClientFactory

load_dotenv()

def main():
  client = BedrockClientFactory().get_client()
  prompt = "Write a short story about a cat."
  response = client.invoke_deepseek(prompt=prompt)

  # Print the output
  print(response)

if __name__ == "__main__":
  main()
