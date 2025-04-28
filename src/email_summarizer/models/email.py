from pydantic import BaseModel


class Email(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body_preview: str | None

    def __str__(self) -> str:
        return f"Email(id={self.id}, subject={self.subject}, \
            sender={self.sender}, date={self.date}, snippet={self.snippet})"

    def to_prompt(self) -> str:
        return f"""
        Sender: {self.sender}
        Subject: {self.subject} - {self.snippet}
        Body:
        <body>
            {self.body_preview}
        </body>
        """


class GroupedEmails(BaseModel):
    sender: str
    count: int
