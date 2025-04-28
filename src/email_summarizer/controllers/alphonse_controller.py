import discord

from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.report import EmailReport
from email_summarizer.utils.ai_utils import compile_email_report
from email_summarizer.utils.email_utils import EmailUnavailableError, get_emails
from email_summarizer.utils.grouping_utils import group_emails


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

    print(f"Logged in as {client.user.name} ({client.user.id})")
    print("------")

    channel_id = int(channel_str)

    try:
        # Get the channel object using the ID
        channel = client.get_channel(channel_id)

        if not channel:
            raise ValueError(f"Could not find channel with ID: {channel_id}")

        print(f"Found channel: {channel.name} ({channel.id})")

        try:
            # Get emails and compile report
            emails = get_emails(email_account, max_results=max_emails)
            grouping_payload = group_emails(emails)
            email_report = compile_email_report(
                email_account=email_account,
                emails=grouping_payload.get("ungrouped_emails", []),
                grouped_emails=grouping_payload.get("list_of_grouped_emails", []),
                important_emails=grouping_payload.get("high_priority_emails", []),
            )

            # Send report to channel
            await channel.send(_report_header(email_report))
            if email_report.is_empty():
                await channel.send("*No emails to report.*")
            else:
                # Display high priority emails
                for i, high_priority in enumerate(email_report.high_priority_summaries):
                    await channel.send(
                        f"{i + 1}. ({high_priority.email.sender}) {high_priority.next_steps}"
                    )
                else:
                    await channel.send("*No high priority emails to report.*")

                # Display regular emails
                for i, summary in enumerate(email_report.summaries):
                    await channel.send(
                        f"{i + 1}. ({summary.email.sender}) {summary.body}"
                    )
                else:
                    await channel.send("*No regular emails to report.*")

                # Display grouped emails
                if _any_grouped_emails(email_report):
                    await channel.send("### Grouped Emails")
                    for grouped_email in email_report.grouped_emails:
                        await channel.send(
                            f"- ({grouped_email.sender}) - message count: {grouped_email.count}"
                        )
                else:
                    await channel.send("*No grouped emails to report.*")
            print(f"Message sent to #{channel.name}")
        except EmailUnavailableError as e:
            print(f"Error: {e}")
            await channel.send("Error: Gmail service not available.")
            print("Reported error to channel.")

    except discord.errors.Forbidden:
        print(
            f"Error: Bot doesn't have permissions to send messages in channel ID {channel_id}."
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # After sending the message, close the connection.
        # If you want the bot to stay online for other tasks, remove this line.
        print("Closing bot connection.")
        await client.close()


def _any_grouped_emails(email_report: EmailReport) -> bool:
    return any(grouped_email.count > 0 for grouped_email in email_report.grouped_emails)
