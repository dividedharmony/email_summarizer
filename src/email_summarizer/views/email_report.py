from pydantic import BaseModel

from email_summarizer.services.gmail import Email


class EmailReport(BaseModel):
    emails: list[Email]
