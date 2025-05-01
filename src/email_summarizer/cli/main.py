from dotenv import load_dotenv

from email_summarizer.services.bedrock_client import BedrockClientFactory
from email_summarizer.services.nova_client import NovaClientFactory

load_dotenv()


def main():
    bedrock_client = BedrockClientFactory().get_client()
    nova_client = NovaClientFactory().get_client(bedrock_client=bedrock_client)
    system_prompt = (
        "Act as a creative writing assistant. When the user "
        "provides you with a topic, write a short story about "
        "that topic. The store should be three sentences long."
    )
    prompt = "A rusty old car"
    response = nova_client.invoke(prompt=prompt, system_prompt=system_prompt)

    # Print the output
    print(response)


if __name__ == "__main__":
    main()
