import os

from email_summarizer.models.enums import EmailAccounts


def get_email_address(email_account_type: EmailAccounts) -> str:
    match email_account_type:
        case EmailAccounts.PRIMARY:
            return os.getenv("PRIMARY_EMAIL_ADDRESS")
        case EmailAccounts.NOREPLY:
            return os.getenv("NOREPLY_EMAIL_ADDRESS")
        case EmailAccounts.ALTERNATE:
            return os.getenv("ALTERNATE_EMAIL_ADDRESS")
        case _:
            raise ValueError(f"Invalid email account type: {email_account_type}")
