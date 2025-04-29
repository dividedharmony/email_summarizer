from typing import TypedDict

from email_summarizer.models.email import Email
from email_summarizer.utils.redaction_utils import redact_pii


class EmailPromptPayload(TypedDict):
    prompt_body: str
    was_redacted: bool


def email_to_prompt(
    email: Email, disable_redaction: bool = False
) -> EmailPromptPayload:
    body = email.body_preview
    was_redacted = False
    if isinstance(body, str) and not disable_redaction:
        payload = redact_pii(body)
        was_redacted = payload["was_redacted"]
        body = payload["final_body"]
    return {
        "prompt_body": f"""\
Sender: <sender>{email.sender}</sender>
Subject: <subject>{email.subject} - {email.snippet}</subject>
Body:
<body>
    {body}
</body>""",
        "was_redacted": was_redacted,
    }
