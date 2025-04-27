import os

from google.oauth2.credentials import Credentials

from email_summarizer.models.enums import EmailAccounts

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # Read-only access

TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_gmail_credentials(email_account: EmailAccounts) -> Credentials:
    return Credentials(
        token=None,
        token_uri=TOKEN_URI,
        refresh_token=_get_env_var(email_account, "REFRESH_TOKEN"),
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        scopes=SCOPES,
    )


def _get_env_var(email_account: EmailAccounts, suffix: str) -> str:
    return os.getenv(f"{email_account.value}_GMAIL_{suffix}")
