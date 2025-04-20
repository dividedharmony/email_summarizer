import asyncio  # Required for discord.py v2.0+ even for simple tasks
import os

import discord
import pystache  # type: ignore
from dotenv import load_dotenv

from email_summarizer.services.gmail import (Email, authenticate_gmail,
                                             list_emails)
from email_summarizer.views.email_report import EmailReport  # type: ignore

if __name__ == "__main__":
    load_dotenv()
# --- Configuration ---
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
if not isinstance(channel_id_str, str):
    raise ValueError("DISCORD_CHANNEL_ID is not a string")
CHANNEL_ID = int(channel_id_str)
MESSAGE_TO_SEND = "Hello from my Python App!"
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


class EmailUnavailableError(Exception):
    pass


def get_emails():
    gmail_service = authenticate_gmail()
    if not gmail_service:
        raise EmailUnavailableError("Gmail service not available.")
    emails = list_emails(gmail_service, max_results=5)
    return emails


def compose_report(emails: list[Email]):
    email_report = EmailReport(emails=emails)
    template = pystache.Renderer().render(email_report)
    return template


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

        if channel:
            print(f"Found channel: {channel.name} ({channel.id})")

            try:
                emails = get_emails()
                report = compose_report(emails)
                # Send the message
                await channel.send(report)
                print(f"Message sent to #{channel.name}")
            except EmailUnavailableError as e:
                print(f"Error: {e}")
                await channel.send("Error: Gmail service not available.")
                print("Reported error to channel.")
        else:
            print(f"Could not find channel with ID: {CHANNEL_ID}")
            print("Please check:")
            print("1. If the CHANNEL_ID is correct.")
            print(
                "2. If the bot has 'View Channel' and 'Send Messages' permissions for that channel."
            )
            print(
                "3. If the bot has been invited to the server containing the channel."
            )

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


async def run_bot():
    """Handles login and potential errors"""
    try:
        await client.start(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(
            "\nError: Improper token passed. Make sure you have the correct BOT_TOKEN."
        )
    except Exception as e:
        print(f"An unexpected error occurred during bot startup or runtime: {e}")


# Run the bot
if __name__ == "__main__":
    asyncio.run(run_bot())
