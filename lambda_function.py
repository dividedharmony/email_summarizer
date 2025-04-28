import asyncio
import json
import logging
import os

from email_summarizer.app import run_bot
from email_summarizer.models.enums import EmailAccounts

ACCOUNT_PARAM_KEY = "email_account_type"

LOG = logging.getLogger()
log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level_name, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)


class MalformedEventError(Exception):
    pass


def lambda_handler(event, _context):
    """
    AWS Lambda handler function.

    :param event: Event data passed by the trigger.
    :param context: Runtime information.
    :return: Response object (structure depends on the trigger, often a dict).
    """
    LOG.info("Received event: %s", json.dumps(event, indent=2))
    status_good = True
    error_message = ""
    try:
        email_account = _parse_email_account_from_event(event)
        asyncio.run(run_bot(email_account))
    except Exception as e:
        LOG.error("Error: %s", e)
        status_good = False
        error_message = str(e)

    response_message = (
        "Email summarizer ran successfully" if status_good else error_message
    )
    response = {
        "statusCode": 200 if status_good else 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": response_message,
            }
        ),
    }
    return response


def _parse_email_account_from_event(event: dict) -> EmailAccounts:
    if "body" not in event:
        raise MalformedEventError("Event body is missing")
    raw_email_account = None
    if isinstance(event.get("body"), str):
        try:
            parsed_body = json.loads(event["body"])
            raw_email_account = parsed_body.get(ACCOUNT_PARAM_KEY)

        except json.JSONDecodeError as json_error:
            raise MalformedEventError(
                f"Event body is not a valid JSON string: {str(json_error)}"
            )
    elif isinstance(event.get("body"), dict):
        raw_email_account = event["body"].get(ACCOUNT_PARAM_KEY)

    if raw_email_account is None:
        raise MalformedEventError(
            "Event body cannot be parsed as a valid email account"
        )

    return EmailAccounts(raw_email_account)
