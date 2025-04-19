import base64
import logging
import os
import os.path
from typing import Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from pydantic import BaseModel

if __name__ == "__main__":
    load_dotenv()

# --- Configuration ---
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # Read-only access
CLIENT_SECRET_FILE = "client_secret.json"  # Path to your client secret file
TOKEN_FILE = "token.json"  # Stores the user's access and refresh tokens
# --- End Configuration ---

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def load_credentials_from_file() -> Optional[Credentials]:
    """Load credentials from the token file if it exists.

    Returns:
        Optional[Credentials]: The loaded credentials or None if loading fails
    """
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except ValueError as e:
        logger.error(f"Error loading token file: {e}. Attempting re-authentication.")
        return None


def refresh_credentials(creds: Credentials) -> Optional[Credentials]:
    """Refresh expired credentials if possible.

    Args:
        creds: The credentials to refresh

    Returns:
        Optional[Credentials]: Refreshed credentials or None if refresh fails
    """
    if not (creds and creds.expired and creds.refresh_token):
        return None

    try:
        logger.info("Credentials expired, refreshing...")
        creds.refresh(Request())
        logger.info("Credentials refreshed.")
        return creds
    except Exception as e:
        logger.error(f"An error occurred during token refresh: {e}")
        return None


def create_new_credentials() -> Optional[Credentials]:
    """Create new credentials through the OAuth flow.

    Returns:
        Optional[Credentials]: New credentials or None if creation fails
    """
    if not os.path.exists(CLIENT_SECRET_FILE):
        logger.error(
            f"Error: {CLIENT_SECRET_FILE} not found. Please download it from Google Cloud Console."
        )
        return None

    try:
        logger.info(f"Starting authentication flow using {CLIENT_SECRET_FILE}...")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        # Note: port=0 finds a random free port
        creds = flow.run_local_server(port=0)
        logger.info("Authentication successful.")
        return creds
    except Exception as e:
        logger.error(f"Error during authentication flow: {e}")
        return None


def save_credentials(creds: Credentials | None) -> bool:
    """Save credentials to the token file.

    Args:
        creds: The credentials to save

    Returns:
        bool: True if saving was successful, False otherwise
    """
    if not creds:
        return False

    try:
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Credentials saved to {TOKEN_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving token file: {e}")
        return False


def build_gmail_service(creds: Credentials | None):
    """Build and return the Gmail API service.

    Args:
        creds: The credentials to use for the service

    Returns:
        The Gmail API service or None if building fails
    """
    if not creds:
        return None

    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service created successfully.")
        return service
    except HttpError as error:
        logger.error(f"An error occurred building the service: {error}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred building the service: {e}")
        return None


def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Handles user authentication and returns the Gmail API service object.

    Returns:
        The Gmail API service or None if authentication fails
    """
    # Try to load existing credentials
    creds = load_credentials_from_file()

    # If credentials are invalid or don't exist, handle authentication
    if not creds or not creds.valid:
        # Try to refresh expired credentials
        if creds:
            creds = refresh_credentials(creds)

        # If refresh failed or credentials don't exist, create new ones
        if not creds:
            creds = create_new_credentials()

        # Save new credentials if we got them
        if creds:
            save_credentials(creds)
        else:
            logger.error("Failed to obtain credentials.")
            return None

    # Build and return the service
    return build_gmail_service(creds)


def list_messages(service, max_results=10):
    """List messages from the user's inbox.

    Args:
        service: The Gmail API service
        max_results: Maximum number of messages to retrieve

    Returns:
        List of message IDs or empty list if no messages found
    """
    if not service:
        logger.error("Gmail service not available.")
        return []

    try:
        # Call the Gmail API to list messages
        # 'me' is a special value indicating the authenticated user
        # We request INBOX labels and limit results
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            logger.info("No messages found.")
            return []

        logger.info(f"Found {len(messages)} messages.")
        return messages
    except HttpError as error:
        logger.error(f"An API error occurred listing messages: {error}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred listing messages: {e}")
        return []


def get_message_details(service, message_id):
    """Get detailed information about a specific message.

    Args:
        service: The Gmail API service
        message_id: The ID of the message to retrieve

    Returns:
        The message details or None if retrieval fails
    """
    if not service or not message_id:
        return None

    try:
        # Get the full message details
        # format='metadata' gets headers only (faster)
        # format='full' gets headers, body, structure
        # format='raw' gets the raw RFC 2822 message (needs parsing)
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",  # Request more details including snippet/payload
            )
            .execute()
        )
        return message
    except HttpError as error:
        logger.error(f"An error occurred fetching message ID {message_id}: {error}")
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred processing message ID {message_id}: {e}"
        )
        return None


def extract_headers(message):
    """Extract headers from a message.

    Args:
        message: The message object from the Gmail API

    Returns:
        Dictionary containing subject, sender, and date
    """
    if not message or "payload" not in message:
        return {"subject": "No Subject", "sender": "No Sender", "date": "No Date"}

    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = next(
        (h["value"] for h in headers if h["name"].lower() == "subject"),
        "No Subject",
    )
    sender = next(
        (h["value"] for h in headers if h["name"].lower() == "from"),
        "No Sender",
    )
    date = next(
        (h["value"] for h in headers if h["name"].lower() == "date"),
        "No Date",
    )

    return {"subject": subject, "sender": sender, "date": date}


def extract_body_data(message):
    """Extract the body data from a message.

    Args:
        message: The message object from the Gmail API

    Returns:
        The body data as a string or None if not found
    """
    if not message or "payload" not in message:
        return None

    payload = message.get("payload", {})

    # Check for multipart message
    if "parts" in payload:
        # It's a multipart message, look for text/plain or text/html
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    return body_data
            elif part["mimeType"] == "text/html":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    return body_data
    # Check for simple message
    elif "body" in payload:
        # It's a simple message
        return payload.get("body", {}).get("data")

    return None


def decode_body(body_data):
    """Decode Base64 encoded body data.

    Args:
        body_data: Base64 encoded body data

    Returns:
        Decoded body text or None if decoding fails
    """
    if not body_data:
        return None

    try:
        # Decode Base64
        return base64.urlsafe_b64decode(body_data).decode("utf-8")
    except Exception as e:
        logger.error(f"Error decoding body: {e}")
        return None


def format_message_info(email: Email):
    """Format message information for display.

    Args:
        email: The email object


    Returns:
        Formatted string with message information
    """
    info = [
        f"ID: {email.id}",
        f"Subject: {email.subject}",
        f"From: {email.sender}",
        f"Date: {email.date}",
        f"Snippet: {email.snippet}",
    ]

    if email.body_preview:
        info.append(f"Body (first 100 chars): {email.body_preview}...")

    return "\n".join(info)


def build_email_from_message(msg_id: str, message: dict) -> Email:
    headers = extract_headers(message)
    snippet = message.get("snippet", "No snippet available.")
    body_data = extract_body_data(message)
    body_preview = None
    if body_data:
        decoded_body = decode_body(body_data)
        if decoded_body:
            body_preview = decoded_body[:100]
    return Email(
        id=msg_id,
        subject=headers["subject"],
        sender=headers["sender"],
        date=headers["date"],
        snippet=snippet,
        body_preview=body_preview,
    )


def list_emails(service, max_results=10) -> list[Email]:
    """Lists the user's email messages and prints basic info."""
    if not service:
        logger.error("Gmail service not available.")
        return []

    messages = list_messages(service, max_results)
    if not messages:
        return []

    emails = []
    for message_info in messages:
        msg_id = message_info["id"]

        # Get message details
        message = get_message_details(service, msg_id)
        if not message:
            continue

        email = build_email_from_message(msg_id, message)
        if email:
            emails.append(email)

    return emails


def read_emails(emails: list[Email]):
    logger.info(f"\nFetching details for the latest {len(emails)} messages:")
    logger.info("-" * 30)

    for email in emails:
        logger.info(email)
        logger.info("-" * 30)

        # Format and display message info
        message_info = format_message_info(email)
        logger.info(message_info)
        logger.info("-" * 30)


if __name__ == "__main__":
    gmail_service = authenticate_gmail()
    if gmail_service:
        emails = list_emails(gmail_service, max_results=5)
        read_emails(emails)
