import os
import re
from typing import TypedDict

from pydantic import BaseModel

from email_summarizer.models.email import Email, GroupedEmails


class GroupingCategory(BaseModel):
    regex: re.Pattern
    name: str
    sender: str | None = None
    count: int
    high_priority: bool = False


def _build_grouping_categories() -> list[GroupingCategory]:
    spouse_regex = re.compile(os.getenv("SPOUSE_REGEX"), re.IGNORECASE)
    daycare_regex = re.compile(os.getenv("DAYCARE_REGEX"), re.IGNORECASE)
    return [
        GroupingCategory(
            regex=re.compile(r"warhorn"),
            name="Warhorn",
            sender=None,
            count=0,
        ),
        GroupingCategory(
            regex=re.compile(r"nextdoor"),
            name="Nextdoor",
            sender=None,
            count=0,
        ),
        GroupingCategory(
            regex=spouse_regex,
            name="Spouse",
            sender=None,
            count=0,
            high_priority=True,
        ),
        GroupingCategory(
            regex=daycare_regex,
            name="Daycare",
            sender=None,
            count=0,
            high_priority=True,
        ),
    ]


class GroupingPayload(TypedDict):
    list_of_grouped_emails: list[GroupedEmails]
    ungrouped_emails: list[Email]
    high_priority_emails: list[Email]


def group_emails(emails: list[Email]) -> GroupingPayload:
    grouped_emails: list[GroupedEmails] = []
    high_priority_emails: list[Email] = []
    ungrouped_emails: list[Email] = []
    grouping_categories = _build_grouping_categories()
    for email in emails:
        for grouping_category in grouping_categories:
            if re.search(grouping_category.regex, email.sender):
                grouping_category.count += 1
                if grouping_category.sender is None:
                    grouping_category.sender = email.sender
                if grouping_category.high_priority:
                    high_priority_emails.append(email)
                break
        else:
            ungrouped_emails.append(email)
    # end for loop

    for grouping_category in grouping_categories:
        if grouping_category.count > 0 and not grouping_category.high_priority:
            grouped_emails.append(
                GroupedEmails(
                    sender=grouping_category.sender or grouping_category.name,
                    count=grouping_category.count,
                )
            )
    return GroupingPayload(
        list_of_grouped_emails=grouped_emails,
        ungrouped_emails=ungrouped_emails,
        high_priority_emails=high_priority_emails,
    )
