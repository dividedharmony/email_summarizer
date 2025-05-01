import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from email_summarizer.models.actionable_email import ActionableEmail
from email_summarizer.models.email import Email, GroupedEmails
from email_summarizer.models.enums import EmailAccounts, SupportedModel
from email_summarizer.models.report import EmailReport
from email_summarizer.models.summary import Summary
from email_summarizer.prompts.next_steps import next_steps_system_prompt
from email_summarizer.prompts.summary_prompt import summary_system_prompt
from email_summarizer.services.anthropic_client import (
    AnthropicClient,
    AnthropicModels,
)
from email_summarizer.services.base_model_client import AbstractModelClient
from email_summarizer.utils.email_utils import email_to_prompt

LOG = logging.getLogger()
ET_TIMEZONE = ZoneInfo("America/New_York")


def build_summary(client: AbstractModelClient, email: Email) -> Summary:
    prompt_payload = email_to_prompt(email)
    response = client.invoke(
        prompt=prompt_payload["prompt_body"],
        system_prompt=summary_system_prompt(prompt_payload["was_redacted"]),
    )
    return Summary(body=response.response, email=email)


def build_actionable_email(
    client: AbstractModelClient, email: Email
) -> ActionableEmail:
    prompt_payload = email_to_prompt(email)
    response = client.invoke(
        prompt=prompt_payload["prompt_body"],
        system_prompt=next_steps_system_prompt(prompt_payload["was_redacted"]),
    )
    return ActionableEmail(next_steps=response.response, email=email)


def compile_email_report(
    client: AbstractModelClient,
    email_account: EmailAccounts,
    emails: list[Email],
    grouped_emails: list[GroupedEmails],
    high_priority_emails: list[Email],
) -> EmailReport:
    LOG.info("Compiling email report...")

    summaries: list[Summary] = []
    actionable_emails: list[ActionableEmail] = []

    LOG.debug("Building summaries of regular emails...")
    for email in emails:
        summary = build_summary(client, email)
        summaries.append(summary)

    LOG.debug("Building actionable emails from high priority emails...")
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


def get_model_client(target_model: SupportedModel) -> AbstractModelClient:
    LOG.debug("Using model: %s", target_model)
    if target_model == SupportedModel.CLAUDE_HAIKU:
        return AnthropicClient(model_name=AnthropicModels.HAIKU)
    elif target_model == SupportedModel.CLAUDE_SONNET:
        return AnthropicClient(model_name=AnthropicModels.SONNET)
    else:
        raise ValueError(f"Unsupported model: {target_model}")
