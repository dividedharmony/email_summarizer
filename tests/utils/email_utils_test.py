from unittest.mock import patch

from ..base import BaseTestCase
from email_summarizer.models.email import Email
from email_summarizer.utils.email_utils import email_to_prompt


class TestEmailUtils(BaseTestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_email = Email(
            id="test-id-123",
            subject="Test Subject",
            sender="test@example.com",
            date="2023-01-01T12:00:00Z",
            snippet="This is a test email snippet",
            body_preview="This is the body of the test email.",
        )

        self.test_email_no_body = Email(
            id="test-id-456",
            subject="Test Subject No Body",
            sender="test2@example.com",
            date="2023-01-02T12:00:00Z",
            snippet="This is another test email snippet",
            body_preview=None,
        )

    def test_email_to_prompt_with_redaction(self):
        """Test email_to_prompt with redaction enabled"""
        with patch("email_summarizer.utils.email_utils.redact_pii") as mock_redact:
            # Configure the mock to return a specific value
            mock_redact.return_value = {
                "was_redacted": True,
                "final_body": "This is the REDACTED body of the test email.",
            }

            result = email_to_prompt(self.test_email)

            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertIn("prompt_body", result)
            self.assertIn("was_redacted", result)
            self.assertTrue(result["was_redacted"])

            # Verify the prompt body format
            self.assertIn("<sender>test@example.com</sender>", result["prompt_body"])
            self.assertIn(
                "<subject>Test Subject - This is a test email snippet</subject>",
                result["prompt_body"],
            )
            self.assertIn("<body>", result["prompt_body"])
            self.assertIn(
                "This is the REDACTED body of the test email.", result["prompt_body"]
            )

            # Verify the mock was called with the correct argument
            mock_redact.assert_called_once_with("This is the body of the test email.")

    def test_email_to_prompt_without_redaction(self):
        """Test email_to_prompt with redaction disabled"""
        with patch("email_summarizer.utils.email_utils.redact_pii") as mock_redact:
            result = email_to_prompt(self.test_email, disable_redaction=True)

            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertIn("prompt_body", result)
            self.assertIn("was_redacted", result)
            self.assertFalse(result["was_redacted"])

            # Verify the prompt body format
            self.assertIn("<sender>test@example.com</sender>", result["prompt_body"])
            self.assertIn(
                "<subject>Test Subject - This is a test email snippet</subject>",
                result["prompt_body"],
            )
            self.assertIn("<body>", result["prompt_body"])
            self.assertIn("This is the body of the test email.", result["prompt_body"])

            # Verify the mock was not called
            mock_redact.assert_not_called()

    def test_email_to_prompt_with_none_body(self):
        """Test email_to_prompt with a None body_preview"""
        result = email_to_prompt(self.test_email_no_body)

        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("prompt_body", result)
        self.assertIn("was_redacted", result)
        self.assertFalse(result["was_redacted"])

        # Verify the prompt body format
        self.assertIn("<sender>test2@example.com</sender>", result["prompt_body"])
        self.assertIn(
            "<subject>Test Subject No Body - This is another test email snippet</subject>",
            result["prompt_body"],
        )
        self.assertIn("<body>", result["prompt_body"])
        self.assertIn("None", result["prompt_body"])

    def test_email_to_prompt_return_type(self):
        """Test that email_to_prompt returns the correct type"""
        result = email_to_prompt(self.test_email)
        self.assertIsInstance(result, dict)
        # Check that it matches the EmailPromptPayload TypedDict structure
        self.assertIn("prompt_body", result)
        self.assertIn("was_redacted", result)
        self.assertIsInstance(result["prompt_body"], str)
        self.assertIsInstance(result["was_redacted"], bool)
