import os
import re


def _get_env_var(key: str) -> str:
    var = os.getenv(key)
    if var is None:
        raise ValueError(f"{key} is not set")
    return var


LICENSE_PLATE_REGEX = re.compile(_get_env_var("LICENSE_PLATE_REGEX"), re.IGNORECASE)
LICENSE_PLATE_REDACTION = "<LICENSE_PLATE>"

ALL_REDACTIONS = [
    {
        "name": "Vehicle License Plate",
        "regex": LICENSE_PLATE_REGEX,
        "redaction": LICENSE_PLATE_REDACTION,
    },
]


REDACTION_PROMPT = f"""
## Personal Information Redaction

Some emails contain personal information that has been redacted.

Below is a list of types of personal information and the corresponding redaction string.
{
    "\n".join(
        [
            f"- {redaction['name']}: {redaction['redaction']}" for redaction in ALL_REDACTIONS
        ]
    )
}

Do not output the redaction string in the output. Do not comment on the redaction.
"""
