from pydantic import BaseModel

from email_summarizer.models.email import Email


class Summary(BaseModel):
    body: str
    email: Email
