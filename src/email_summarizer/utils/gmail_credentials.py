import os

from google.oauth2.credentials import Credentials

from email_summarizer.models.enums import EmailAccounts


def build_gmail_credentials(email_account: EmailAccounts) -> Credentials:
    return Credentials(
        token=_get_env_var(email_account, "TOKEN"),
        refresh_token=_get_env_var(email_account, "REFRESH_TOKEN"),
        client_id=_get_env_var(email_account, "CLIENT_ID"),
        client_secret=_get_env_var(email_account, "CLIENT_SECRET"),
    )


def _get_env_var(email_account: EmailAccounts, suffix: str) -> str:
    return os.getenv(f"{email_account.value}_GMAIL_{suffix}")
