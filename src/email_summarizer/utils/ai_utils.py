from datetime import datetime
from zoneinfo import ZoneInfo

from email_summarizer.models.actionable_email import ActionableEmail
from email_summarizer.models.email import Email, GroupedEmails
from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.report import EmailReport
from email_summarizer.models.summary import Summary
from email_summarizer.prompts.next_steps import NEXT_STEPS_PROMPT
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


def build_actionable_email(
    client: BedrockReasoningClient, email: Email
) -> ActionableEmail:
    prompt = email_to_prompt(email)
    response = client.invoke_model(prompt=prompt, system_prompt=NEXT_STEPS_PROMPT)
    return ActionableEmail(next_steps=response.response, email=email)


def compile_email_report(
    email_account: EmailAccounts,
    emails: list[Email],
    grouped_emails: list[GroupedEmails],
    high_priority_emails: list[Email],
) -> EmailReport:
    client = BedrockReasoningClient(model_name=AnthropicModels.HAIKU)
    summaries: list[Summary] = []
    actionable_emails: list[ActionableEmail] = []
    for email in emails:
        summary = build_summary(client, email)
        summaries.append(summary)

    # Turn high priority emails into actionable emails
    for email in high_priority_emails:
        actionable_email = build_actionable_email(client, email)
        actionable_emails.append(actionable_email)
    return EmailReport(
        email_account=email_account,
        summaries=summaries,
        timestamp=datetime.now(tz=ET_TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        grouped_emails=grouped_emails,
        actionable_emails=actionable_emails,
    )
