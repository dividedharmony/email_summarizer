import asyncio  # Required for discord.py v2.0+ even for simple tasks
import os

import discord
from dotenv import load_dotenv

from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.report import EmailReport
from email_summarizer.utils.ai_utils import summarize_emails
from email_summarizer.utils.email_utils import (
    EmailUnavailableError,
    get_emails,
    group_en_masse_emails,
)

if __name__ == "__main__":
    load_dotenv()
# --- Configuration ---
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
if not isinstance(channel_id_str, str):
    raise ValueError("DISCORD_CHANNEL_ID is not a string")
CHANNEL_ID = int(channel_id_str)
MAX_EMAILS = int(os.getenv("MAX_EMAILS", 5))
# --- End Configuration ---

# Define necessary intents
# discord.py v2.0 requires explicit intent declaration
intents = discord.Intents.default()
# If you don't need to read message content or member lists,
# default intents are often enough for just sending.
# If you needed members intent later: intents.members = True
# If you needed message content intent later: intents.message_content = True

# Create a client instance with the specified intents
client = discord.Client(intents=intents)


def _report_header(email_report: EmailReport) -> str:
    return f"# {email_report.email_account.value} Email Report {email_report.timestamp}"


@client.event
async def on_ready():
    """
    This function runs when the bot successfully connects to Discord.
    """
    print(f"Logged in as {client.user.name} ({client.user.id})")
    print("------")

    try:
        # Get the channel object using the ID
        channel = client.get_channel(CHANNEL_ID)
        # Get the email account set in run_bot
        email_account = client.target_email_account

        if not channel:
            raise ValueError(f"Could not find channel with ID: {CHANNEL_ID}")

        if not email_account:
            raise ValueError("Email account not set.")

        print(f"Found channel: {channel.name} ({channel.id})")

        try:
            emails = get_emails(email_account, max_results=MAX_EMAILS)
            grouping_payload = group_en_masse_emails(emails)
            email_report = summarize_emails(
                email_account=email_account,
                emails=grouping_payload.get("ungrouped_emails", []),
                grouped_emails=grouping_payload.get("list_of_grouped_emails", []),
            )
            await channel.send(_report_header(email_report))
            if email_report.is_empty():
                await channel.send("No emails to report.")
            else:
                for i, summary in enumerate(email_report.summaries):
                    await channel.send(
                        f"{i + 1}. ({summary.email.sender}) {summary.body}"
                    )
                await channel.send("### Grouped Emails")
                for grouped_email in email_report.grouped_emails:
                    await channel.send(
                        f"- ({grouped_email.sender}) {grouped_email.count}"
                    )
            print(f"Message sent to #{channel.name}")
        except EmailUnavailableError as e:
            print(f"Error: {e}")
            await channel.send("Error: Gmail service not available.")
            print("Reported error to channel.")

    except discord.errors.Forbidden:
        print(
            f"Error: Bot doesn't have permissions to send messages in channel ID {CHANNEL_ID}."
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # After sending the message, close the connection.
        # If you want the bot to stay online for other tasks, remove this line.
        print("Closing bot connection.")
        await client.close()


async def run_bot(email_account_type: str):
    """Handles login and potential errors"""
    email_account = EmailAccounts(email_account_type)
    try:
        client.target_email_account = email_account
        await client.start(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(
            "\nError: Improper token passed. Make sure you have the correct BOT_TOKEN."
        )
    except Exception as e:
        print(f"An unexpected error occurred during bot startup or runtime: {e}")


# Run the bot
if __name__ == "__main__":
    email_account_type = EmailAccounts.PRIMARY.value
    asyncio.run(run_bot(email_account_type))
