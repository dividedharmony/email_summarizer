from pydantic import BaseModel

from email_summarizer.models.email import Email


class ActionableEmail(BaseModel):
    email: Email
    next_steps: str
