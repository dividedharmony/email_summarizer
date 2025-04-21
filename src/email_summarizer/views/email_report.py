from pydantic import BaseModel

from email_summarizer.services.gmail import Email


class EmailReport(BaseModel):
    summaries: list[str]
    emails: list[Email]
    today: str
