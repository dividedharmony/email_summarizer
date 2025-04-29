import os
import re

from pydantic import BaseModel


def _get_env_var(key: str) -> str:
    var = os.getenv(key)
    if var is None:
        raise ValueError(f"{key} is not set")
    return var


LICENSE_PLATE_REGEX = _get_env_var("LICENSE_PLATE_REGEX")
STREET_ADDRESS_REGEX = _get_env_var("STREET_ADDRESS_REGEX")


class RedactionInfo(BaseModel):
    name: str
    regex_str: str
    redaction: str

    @property
    def regex(self) -> re.Pattern:
        return re.compile(self.regex_str, re.IGNORECASE)


ALL_REDACTIONS: list[RedactionInfo] = [
    RedactionInfo(
        name="Vehicle License Plate",
        regex_str=LICENSE_PLATE_REGEX,
        redaction="<LICENSE_PLATE>",
    ),
    RedactionInfo(
        name="Social Security Number",
        regex_str=r"\b\d{3}-?\d{2}-?\d{4}\b",
        redaction="<SSN>",
    ),
    RedactionInfo(
        name="Phone Number",
        regex_str=r"(\(\d{3}\)|\d{3})?[- ]?\d{3}[- ]?\d{4}\b",
        redaction="<PHONE_NUMBER>",
    ),
    RedactionInfo(
        name="Street Address",
        regex_str=STREET_ADDRESS_REGEX,
        redaction="<ADDRESS>",
    ),
]


REDACTION_PROMPT = f"""
## Personal Information Redaction

Some emails contain personal information that has been redacted.

Below is a list of types of personal information and the corresponding redaction string.
{
    "\n".join(
        [
            f"- {redaction.name}: {redaction.redaction}" for redaction in ALL_REDACTIONS
        ]
    )
}

Do not output the redaction string in the output. Do not comment on the redaction.
"""


def combined_redactions_regex() -> re.Pattern:
    return re.compile(
        "|".join([redaction.regex_str for redaction in ALL_REDACTIONS]),
        re.IGNORECASE,
    )
