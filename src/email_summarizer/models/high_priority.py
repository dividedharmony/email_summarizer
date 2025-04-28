from pydantic import BaseModel

from email_summarizer.models.email import Email


class HighPriorityEmail(BaseModel):
    email: Email
    next_steps: str
