from pydantic import BaseModel

from email_summarizer.models.summary import Summary


class EmailReport(BaseModel):
    summaries: list[Summary]
    today: str
