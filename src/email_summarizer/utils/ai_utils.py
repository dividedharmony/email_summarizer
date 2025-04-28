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
from email_summarizer.utils.email_utils import email_to_prompt

ET_TIMEZONE = ZoneInfo("America/New_York")


def build_summary(client: BedrockReasoningClient, email: Email) -> Summary:
    response = client.invoke_model(
        prompt=email_to_prompt(email), system_prompt=SUMMARY_PROMPT
    )
    return Summary(body=response.response, email=email)


def build_actionable_email(
    client: BedrockReasoningClient, email: Email
) -> ActionableEmail:
    response = client.invoke_model(
        prompt=email_to_prompt(email), system_prompt=NEXT_STEPS_PROMPT
    )
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
