import re

from email_summarizer.prompts.pii_redaction import (
    LICENSE_PLATE_REDACTION,
    LICENSE_PLATE_REGEX,
)


def redact_pii(email_body: str) -> str:
    """
    Redact PII from the email body.
    """
    redacted_body = re.sub(LICENSE_PLATE_REGEX, LICENSE_PLATE_REDACTION, email_body)
    return redacted_body
