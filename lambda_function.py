import asyncio
import json

from email_summarizer.app import run_bot
from email_summarizer.models.enums import EmailAccounts


class MalformedEventError(Exception):
    pass


def lambda_handler(event, _context):
    """
    AWS Lambda handler function.

    :param event: Event data passed by the trigger.
    :param context: Runtime information.
    :return: Response object (structure depends on the trigger, often a dict).
    """
    print("Received event: " + json.dumps(event, indent=2))
    status_good = True
    error_message = ""
    try:
        email_account = _parse_email_account_from_event(event)
        asyncio.run(run_bot(email_account))
    except Exception as e:
        print(f"Error: {e}")
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
            raw_email_account = json.loads(event["body"])
        except json.JSONDecodeError as json_error:
            raise MalformedEventError(
                f"Event body is not a valid JSON string: {str(json_error)}"
            )
    elif isinstance(event.get("body"), dict):
        raw_email_account = event["body"].get("email_account")

    if raw_email_account is None:
        raise MalformedEventError(
            "Event body cannot be parsed as a valid email account"
        )

    return EmailAccounts(raw_email_account)
