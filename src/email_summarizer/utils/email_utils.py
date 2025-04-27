import re
from typing import TypedDict

from email_summarizer.models.email import Email, GroupedEmails
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


WARHORN_REGEX = r"warhorn"
NEXTDOOR_REGEX = r"nextdoor"


class GroupingPayload(TypedDict):
    list_of_grouped_emails: list[GroupedEmails]
    ungrouped_emails: list[Email]


def group_en_masse_emails(emails: list[Email]) -> GroupingPayload:
    ungrouped_emails = []
    warhorn_emails = []
    nextdoor_emails = []
    grouped_emails = []
    for email in emails:
        if re.search(WARHORN_REGEX, email.sender):
            warhorn_emails.append(email)
        elif re.search(NEXTDOOR_REGEX, email.sender):
            nextdoor_emails.append(email)
        else:
            ungrouped_emails.append(email)
    # end for loop

    if len(warhorn_emails) > 0:
        grouped_emails.append(
            GroupedEmails(sender=warhorn_emails[0].sender, count=len(warhorn_emails))
        )
    if len(nextdoor_emails) > 0:
        grouped_emails.append(
            GroupedEmails(sender=nextdoor_emails[0].sender, count=len(nextdoor_emails))
        )
    return GroupingPayload(
        list_of_grouped_emails=grouped_emails,
        ungrouped_emails=ungrouped_emails,
    )
