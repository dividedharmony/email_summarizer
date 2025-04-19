from dotenv import load_dotenv

from email_summarizer.services.bedrock_client import BedrockClientFactory
# from email_summarizer.services.deepseek_client import DeepseekClientFactory
from email_summarizer.services.sonnet_client import SonnetClientFactory

load_dotenv()


def main():
    bedrock_client = BedrockClientFactory().get_client()
    # deepseek_client = DeepseekClientFactory().get_client(bedrock_client=bedrock_client)
    sonnet_client = SonnetClientFactory().get_client(bedrock_client=bedrock_client)
    prompt = "Human: Give me five common American male names\nAssistant:"
    response = sonnet_client.invoke(prompt=prompt)

    # Print the output
    print(response)


if __name__ == "__main__":
    main()
