from datetime import datetime
from zoneinfo import ZoneInfo

from email_summarizer.models.email import Email
from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.report import EmailReport
from email_summarizer.models.summary import Summary
from email_summarizer.prompts.summary_prompt import SUMMARY_PROMPT
from email_summarizer.services.anthropic_client import (
    AnthropicModels,
    BedrockReasoningClient,
)

ET_TIMEZONE = ZoneInfo("America/New_York")


def email_to_prompt(email: Email) -> str:
    return f"""
    Sender: {email.sender}
    Subject: {email.subject} - {email.snippet}
    Body:
      <body>
        {email.body_preview}
      </body>
    """


def build_summary(client: BedrockReasoningClient, email: Email) -> Summary:
    prompt = email_to_prompt(email)
    response = client.invoke_model(prompt=prompt, system_prompt=SUMMARY_PROMPT)
    return Summary(body=response.response, email=email)


def summarize_emails(email_account: EmailAccounts, emails: list[Email]) -> EmailReport:
    client = BedrockReasoningClient(model_name=AnthropicModels.HAIKU)
    summaries = []
    for email in emails:
        summary = build_summary(client, email)
        summaries.append(summary)
    return EmailReport(
        email_account=email_account,
        summaries=summaries,
        today=datetime.now(tz=ET_TIMEZONE).strftime("%Y-%m-%d %H:%M"),
    )
