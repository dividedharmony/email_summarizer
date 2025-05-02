import asyncio  # Required for discord.py v2.0+ even for simple tasks
import logging
import os

import discord
from dotenv import load_dotenv

from email_summarizer.controllers.alphonse_controller import put_email_report
from email_summarizer.models.enums import EmailAccounts, SupportedModel

LOG = logging.getLogger()

if __name__ == "__main__":
    load_dotenv()
# --- Configuration ---
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID")
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


@client.event
async def on_ready():
    """
    This function runs when the bot successfully connects to Discord.
    """
    LOG.info("Discord bot ready")
    email_account = client.target_email_account
    target_model = client.target_model
    await put_email_report(
        client, email_account, target_model, CHANNEL_ID_STR, MAX_EMAILS
    )


async def run_bot(email_account_type: str, model_str: str):
    """Handles login and potential errors"""
    email_account = EmailAccounts(email_account_type)
    target_model = SupportedModel(model_str)
    try:
        LOG.info("Starting Discord bot...")
        client.target_email_account = email_account
        client.target_model = target_model
        await client.start(BOT_TOKEN)
    except discord.errors.LoginFailure:
        LOG.error(
            "Error: Improper token passed. Make sure you have the correct BOT_TOKEN."
        )
    except Exception as e:
        LOG.error(f"An unexpected error occurred during bot startup or runtime: {e}")


# Run the bot
if __name__ == "__main__":
    email_account_type = EmailAccounts.PRIMARY.value
    model_str = SupportedModel.NOVA_MICRO.value
    asyncio.run(run_bot(email_account_type, model_str))
