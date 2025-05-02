import asyncio
import json
import logging
import os
import sys

from email_summarizer.app import run_bot

ACCOUNT_PARAM_KEY = "email_account_type"
MODEL_PARAM_KEY = "model"

LOG = logging.getLogger()
log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level_name, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOG.addHandler(handler)


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
        body = _parse_body_from_event(event)
        email_account = _parse_value_from_body(body, ACCOUNT_PARAM_KEY)
        model = _parse_value_from_body(body, MODEL_PARAM_KEY)
        asyncio.run(run_bot(email_account, model))
    except Exception as e:
        LOG.error("Error: %s", e)
        raise e

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


def _parse_body_from_event(event: dict) -> dict:
    if "body" not in event:
        raise MalformedEventError("Event body is missing")
    if isinstance(event.get("body"), str):
        try:
            return json.loads(event["body"])
        except json.JSONDecodeError as json_error:
            raise MalformedEventError(
                f"Event body is not a valid JSON string: {str(json_error)}"
            )
    elif isinstance(event.get("body"), dict):
        return event["body"]
    else:
        raise MalformedEventError("Event body is not a valid JSON string")


def _parse_value_from_body(body: dict, key: str) -> str:
    raw_value = body.get(key)

    if not isinstance(raw_value, str):
        raise MalformedEventError(
            f"Event body.{key} cannot be parsed as a valid string value"
        )

    return raw_value
