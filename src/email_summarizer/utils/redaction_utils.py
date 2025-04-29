import re
from typing import TypedDict

from email_summarizer.prompts.pii_redaction import ALL_REDACTIONS


class RedactionPayload(TypedDict):
    was_redacted: bool
    final_body: str


def redact_pii(email_body: str) -> str:
    """
    Redact PII from the email body.
    """
    assert isinstance(email_body, str), "email_body must be a string"

    was_redacted = False
    running_body = email_body
    for redaction in ALL_REDACTIONS:
        regex = redaction["regex"]
        running_body, num_subs = re.subn(regex, redaction["redaction"], running_body)
        if num_subs > 0:
            was_redacted = True
    return RedactionPayload(was_redacted=was_redacted, final_body=running_body)
