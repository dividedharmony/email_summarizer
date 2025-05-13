from email_summarizer.models.enums import EmailAccounts
from email_summarizer.services.gmail import authenticate_gmail, list_emails


class EmailUnavailableError(Exception):
    pass


def get_emails(email_account: EmailAccounts, max_results: int):
    """
    Get emails from gmail.

    Args:
        email_account: The email account to get emails from.
        max_results: The maximum number of emails to get.

    Raises:
        EmailUnavailableError: If the gmail service is not available.
        RefreshTokenInvalidError: If the refresh token is invalid.

    Returns:
        A list of emails.
    """
    gmail_service = authenticate_gmail(email_account)
    if not gmail_service:
        raise EmailUnavailableError("Gmail service not available.")
    emails = list_emails(gmail_service, max_results=max_results)
    return emails
