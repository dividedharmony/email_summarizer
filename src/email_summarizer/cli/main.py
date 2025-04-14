from dotenv import load_dotenv
from email_summarizer.services.bedrock_client import BedrockClientFactory
from email_summarizer.services.deepseek_client import DeepseekClientFactory

load_dotenv()

def main():
  bedrock_client = BedrockClientFactory().get_client()
  deepseek_client = DeepseekClientFactory().get_client(bedrock_client=bedrock_client)
  prompt = "Give me five common American male names"
  response = deepseek_client.invoke(prompt=prompt)

  # Print the output
  print(response)

if __name__ == "__main__":
  main()
