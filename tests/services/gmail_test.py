import base64
import unittest
from unittest.mock import MagicMock, patch

from email_summarizer.services.gmail import (
    Email,
    build_email_from_message,
    decode_body,
    extract_headers,
    format_message_info,
    list_emails,
    load_credentials_from_file,
    refresh_credentials,
)


class TestEmail(unittest.TestCase):
    def test_email_creation(self):
        email = Email(
            id="123",
            subject="Test Subject",
            sender="test@example.com",
            date="2024-04-19",
            snippet="Test snippet",
            body_preview="Test body preview",
        )
        self.assertEqual(email.id, "123")
        self.assertEqual(email.subject, "Test Subject")
        self.assertEqual(email.sender, "test@example.com")
        self.assertEqual(email.date, "2024-04-19")
        self.assertEqual(email.snippet, "Test snippet")
        self.assertEqual(email.body_preview, "Test body preview")

    def test_email_str_representation(self):
        email = Email(
            id="123",
            subject="Test Subject",
            sender="test@example.com",
            date="2024-04-19",
            snippet="Test snippet",
            body_preview=None,
        )
        expected_str = "Email(id=123, subject=Test Subject, sender=test@example.com, date=2024-04-19, snippet=Test snippet)"
        self.assertEqual(str(email), expected_str)


class TestGmailService(unittest.TestCase):
    @patch("os.path.exists")
    def test_load_credentials_from_file_not_exists(self, mock_exists):
        mock_exists.return_value = False
        result = load_credentials_from_file()
        self.assertIsNone(result)

    @patch("google.oauth2.credentials.Credentials.from_authorized_user_file")
    @patch("os.path.exists")
    def test_load_credentials_from_file_success(self, mock_exists, mock_from_file):
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_from_file.return_value = mock_creds
        result = load_credentials_from_file()
        self.assertEqual(result, mock_creds)

    @patch("google.oauth2.credentials.Credentials")
    def test_refresh_credentials_not_expired(self, mock_creds_class):
        mock_creds = MagicMock()
        mock_creds.expired = False
        result = refresh_credentials(mock_creds)
        self.assertIsNone(result)

    @patch("google.oauth2.credentials.Credentials")
    def test_refresh_credentials_success(self, mock_creds_class):
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "token"
        result = refresh_credentials(mock_creds)
        self.assertEqual(result, mock_creds)
        mock_creds.refresh.assert_called_once()

    def test_extract_headers_empty_message(self):
        result = extract_headers({})
        self.assertEqual(result["subject"], "No Subject")
        self.assertEqual(result["sender"], "No Sender")
        self.assertEqual(result["date"], "No Date")

    def test_extract_headers_valid_message(self):
        message = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Date", "value": "2024-04-19"},
                ]
            }
        }
        result = extract_headers(message)
        self.assertEqual(result["subject"], "Test Subject")
        self.assertEqual(result["sender"], "test@example.com")
        self.assertEqual(result["date"], "2024-04-19")

    def test_decode_body_success(self):
        test_text = "Hello, World!"
        encoded = base64.urlsafe_b64encode(test_text.encode()).decode()
        result = decode_body(encoded)
        self.assertEqual(result, test_text)

    def test_decode_body_invalid_input(self):
        result = decode_body(None)
        self.assertIsNone(result)

    def test_format_message_info(self):
        email = Email(
            id="123",
            subject="Test Subject",
            sender="test@example.com",
            date="2024-04-19",
            snippet="Test snippet",
            body_preview="Test body preview",
        )
        result = format_message_info(email)
        self.assertIn("ID: 123", result)
        self.assertIn("Subject: Test Subject", result)
        self.assertIn("From: test@example.com", result)
        self.assertIn("Date: 2024-04-19", result)
        self.assertIn("Snippet: Test snippet", result)
        self.assertIn("Body (first 100 chars): Test body preview...", result)

    def test_build_email_from_message(self):
        message = {
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Date", "value": "2024-04-19"},
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Test body").decode()},
            },
        }
        email = build_email_from_message("123", message)
        self.assertEqual(email.id, "123")
        self.assertEqual(email.subject, "Test Subject")
        self.assertEqual(email.sender, "test@example.com")
        self.assertEqual(email.date, "2024-04-19")
        self.assertEqual(email.snippet, "Test snippet")
        self.assertEqual(email.body_preview, "Test body")

    @patch("email_summarizer.services.gmail.list_messages")
    @patch("email_summarizer.services.gmail.get_message_details")
    def test_list_and_read_emails(self, mock_get_details, mock_list_messages):
        mock_service = MagicMock()
        mock_list_messages.return_value = [{"id": "123"}]
        mock_get_details.return_value = {
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Date", "value": "2024-04-19"},
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Test body").decode()},
            },
        }
        list_emails(mock_service, max_results=1)
        mock_list_messages.assert_called_once_with(mock_service, 1)
        mock_get_details.assert_called_once_with(mock_service, "123")


if __name__ == "__main__":
    unittest.main()
