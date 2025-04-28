from email_summarizer.models.enums import EmailAccounts
from email_summarizer.services.gmail import authenticate_gmail, list_emails


class EmailUnavailableError(Exception):
    pass


def get_emails(email_account: EmailAccounts, max_results: int):
    gmail_service = authenticate_gmail(email_account)
    if not gmail_service:
        raise EmailUnavailableError("Gmail service not available.")
    emails = list_emails(gmail_service, max_results=max_results)
    return emails
