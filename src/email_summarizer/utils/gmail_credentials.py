import os

from google.oauth2.credentials import Credentials

from email_summarizer.models.enums import EmailAccounts

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # Read-only access


def build_gmail_credentials(email_account: EmailAccounts) -> Credentials:
    return Credentials(
        token=None,
        refresh_token=_get_env_var(email_account, "REFRESH_TOKEN"),
        token_uri=os.getenv("GMAIL_TOKEN_URI"),  # same for all clients
        client_id=_get_env_var(email_account, "CLIENT_ID"),
        client_secret=_get_env_var(email_account, "CLIENT_SECRET"),
        scopes=SCOPES,
    )


def _get_env_var(email_account: EmailAccounts, suffix: str) -> str:
    return os.getenv(f"{email_account.value}_GMAIL_{suffix}")
