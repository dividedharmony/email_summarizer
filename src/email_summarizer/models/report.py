from pydantic import BaseModel

from email_summarizer.models.email import GroupedEmails
from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.summary import Summary


class EmailReport(BaseModel):
    email_account: EmailAccounts
    summaries: list[Summary]
    timestamp: str
    grouped_emails: list[GroupedEmails]

    def is_empty(self) -> bool:
        return len(self.summaries) == 0 and len(self.grouped_emails) == 0
