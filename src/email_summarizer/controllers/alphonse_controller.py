import logging

import discord

from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.report import EmailReport
from email_summarizer.utils.ai_utils import compile_email_report
from email_summarizer.utils.gmail_utils import EmailUnavailableError, get_emails
from email_summarizer.utils.grouping_utils import group_emails

LOG = logging.getLogger()


def _report_header(email_report: EmailReport) -> str:
    return f"# {email_report.email_account.value} Email Report {email_report.timestamp}"


async def put_email_report(
    client: discord.Client,
    email_account: EmailAccounts,
    channel_str: str,
    max_emails: int,
) -> None:
    """
    Get emails from gmail, compile them into a report, and send the report to the channel.
    """
    # Guard statements
    assert client.user is not None
    assert channel_str is not None
    assert max_emails is not None
    assert email_account is not None

    LOG.info("Logged in as %s (%s)", client.user.name, client.user.id)
    LOG.info("------")

    channel_id = int(channel_str)

    try:
        # Get the channel object using the ID
        channel = client.get_channel(channel_id)

        if not channel:
            raise ValueError(f"Could not find channel with ID: {channel_id}")

        LOG.info("Found channel: %s (%s)", channel.name, channel.id)

        try:
            # Get emails and compile report
            emails = get_emails(email_account, max_results=max_emails)
            grouping_payload = group_emails(emails)
            email_report = compile_email_report(
                email_account=email_account,
                emails=grouping_payload.get("ungrouped_emails", []),
                grouped_emails=grouping_payload.get("list_of_grouped_emails", []),
                high_priority_emails=grouping_payload.get("high_priority_emails", []),
            )

            # Send report to channel
            await channel.send(_report_header(email_report))
            if email_report.is_empty():
                await channel.send("*No emails to report.*")
            else:
                LOG.debug("Displaying actionable emails...")
                if len(email_report.actionable_emails) > 0:
                    for i, actionable_email in enumerate(
                        email_report.actionable_emails
                    ):
                        await channel.send(
                            f"{i + 1}. ({actionable_email.email.sender}) {actionable_email.next_steps}"
                        )
                else:
                    await channel.send("*No high priority emails to report.*")

                LOG.debug("Displaying regular emails...")
                if len(email_report.summaries) > 0:
                    for i, summary in enumerate(email_report.summaries):
                        await channel.send(
                            f"{i + 1}. ({summary.email.sender}) {summary.body}"
                        )
                else:
                    await channel.send("*No regular emails to report.*")

                LOG.debug("Displaying grouped emails...")
                if _any_grouped_emails(email_report):
                    await channel.send("### Grouped Emails")
                    for grouped_email in email_report.grouped_emails:
                        await channel.send(
                            f"- ({grouped_email.sender}) - message count: {grouped_email.count}"
                        )
                else:
                    await channel.send("*No grouped emails to report.*")
            LOG.info("Message sent to %s", channel.name)
        except EmailUnavailableError as e:
            LOG.error("Error: %s", e)
            await channel.send("Error: Gmail service not available.")
            LOG.info("Reported error to channel.")

    except discord.errors.Forbidden:
        LOG.error(
            "Error: Bot doesn't have permissions to send messages in channel ID %s.",
            channel_id,
        )
    except Exception as e:
        LOG.error("An error occurred: %s", e)
    finally:
        # After sending the message, close the connection.
        # If you want the bot to stay online for other tasks, remove this line.
        LOG.info("Closing bot connection.")
        await client.close()


def _any_grouped_emails(email_report: EmailReport) -> bool:
    return any(grouped_email.count > 0 for grouped_email in email_report.grouped_emails)
