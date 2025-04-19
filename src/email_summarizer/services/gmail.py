import base64
import os
import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore

load_dotenv()

# --- Configuration ---
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # Read-only access
CLIENT_SECRET_FILE = "client_secret.json"  # Path to your client secret file
TOKEN_FILE = "token.json"  # Stores the user's access and refresh tokens
# --- End Configuration ---


def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Handles user authentication and returns the Gmail API service object.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except ValueError as e:
            print(f"Error loading token file: {e}. Attempting re-authentication.")
            creds = None  # Force re-authentication if token file is invalid

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Credentials expired, refreshing...")
                creds.refresh(Request())
                print("Credentials refreshed.")
            except Exception as e:
                print(f"An error occurred during token refresh: {e}")
                # Force re-authentication if refresh fails
                creds = None
        else:
            # Only run the flow if client_secret.json exists
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(
                    f"Error: {CLIENT_SECRET_FILE} not found. Please download it from Google Cloud Console."
                )
                return None

            print(
                f"No valid credentials found or refresh failed. \
                    Starting authentication flow using {CLIENT_SECRET_FILE}..."
            )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            # Note: port=0 finds a random free port
            creds = flow.run_local_server(port=0)
            print("Authentication successful.")

        # Save the credentials for the next run
        if creds:
            try:
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                print(f"Credentials saved to {TOKEN_FILE}")
            except Exception as e:
                print(f"Error saving token file: {e}")
        else:
            print("Failed to obtain credentials.")
            return None  # Exit if authentication failed

    # Build and return the Gmail API service
    try:
        service = build("gmail", "v1", credentials=creds)
        print("Gmail API service created successfully.")
        return service
    except HttpError as error:
        print(f"An error occurred building the service: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred building the service: {e}")
        return None


def list_and_read_emails(service, max_results=10):
    """Lists the user's email messages and prints basic info."""
    if not service:
        print("Gmail service not available.")
        return

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
            print("No messages found.")
            return

        print(f"\nFetching details for the latest {len(messages)} messages:")
        print("-" * 30)

        for message_info in messages:
            msg_id = message_info["id"]
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
                        id=msg_id,
                        format="full",  # Request more details including snippet/payload
                    )
                    .execute()
                )

                # Extract headers (Subject, From, Date)
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

                # Get the snippet
                snippet = message.get("snippet", "No snippet available.")

                print(f"ID: {msg_id}")
                print(f"Subject: {subject}")
                print(f"From: {sender}")
                print(f"Date: {date}")
                print(f"Snippet: {snippet}")

                # --- Accessing Email Body (Example) ---
                body_data = None
                if "parts" in payload:
                    # It's a multipart message, look for text/plain or text/html
                    for part in payload["parts"]:
                        if part["mimeType"] == "text/plain":
                            body_data = part.get("body", {}).get("data")
                            break  # Prefer plain text
                        elif part["mimeType"] == "text/html":
                            body_data = part.get("body", {}).get(
                                "data"
                            )  # Fallback to HTML
                elif "body" in payload:
                    # It's a simple message
                    body_data = payload.get("body", {}).get("data")

                if body_data:
                    try:
                        # Decode Base64
                        decoded_body = base64.urlsafe_b64decode(body_data).decode(
                            "utf-8"
                        )
                        print(f"Body (first 100 chars): {decoded_body[:100]}...")
                    except Exception as decode_error:
                        print(f"Error decoding body: {decode_error}")
                else:
                    print("Body data not found in expected parts.")
                # --- End Body Accessing ---

                print("-" * 30)

            except HttpError as error:
                print(f"An error occurred fetching message ID {msg_id}: {error}")
            except Exception as e:
                print(
                    f"An unexpected error occurred processing message ID {msg_id}: {e}"
                )

    except HttpError as error:
        print(f"An API error occurred: {error}")
    except Exception as e:
        print(f"An unexpected error occurred listing messages: {e}")


if __name__ == "__main__":
    gmail_service = authenticate_gmail()
    if gmail_service:
        list_and_read_emails(gmail_service, max_results=5)  # List latest 5 emails
