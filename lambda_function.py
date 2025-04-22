import asyncio
import json

from email_summarizer.app import run_bot


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
        asyncio.run(run_bot())
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
