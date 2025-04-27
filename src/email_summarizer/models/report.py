from pydantic import BaseModel

from email_summarizer.models.enums import EmailAccounts
from email_summarizer.models.summary import Summary


class EmailReport(BaseModel):
    email_account: EmailAccounts
    summaries: list[Summary]
    today: str
