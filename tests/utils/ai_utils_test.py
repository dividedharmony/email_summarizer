from unittest.mock import patch, MagicMock

from ..base import BaseTestCase
from email_summarizer.models.email import Email, GroupedEmails
from email_summarizer.models.enums import EmailAccounts, SupportedModel
from email_summarizer.models.summary import Summary
from email_summarizer.models.actionable_email import ActionableEmail
from email_summarizer.models.report import EmailReport
from email_summarizer.utils.ai_utils import (
    build_summary,
    build_actionable_email,
    compile_email_report,
    get_model_client,
)
from email_summarizer.services.anthropic_client import (
    BedrockReasoningClient,
    AnthropicModels,
)


class TestAiUtils(BaseTestCase):
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

        self.mock_client = MagicMock(spec=BedrockReasoningClient)
        self.mock_response = MagicMock()
        self.mock_response.response = "This is a test summary"
        self.mock_client.invoke_model.return_value = self.mock_response

    def test_build_summary(self):
        """Test building a summary from an email"""
        with patch(
            "email_summarizer.utils.ai_utils.email_to_prompt"
        ) as mock_email_to_prompt:
            mock_email_to_prompt.return_value = {
                "prompt_body": "Test prompt body",
                "was_redacted": False,
            }

            summary = build_summary(self.mock_client, self.test_email)

            # Verify the summary was created correctly
            self.assertIsInstance(summary, Summary)
            self.assertEqual(summary.body, "This is a test summary")
            self.assertEqual(summary.email, self.test_email)

            # Verify the client was called correctly
            self.mock_client.invoke_model.assert_called_once()
            call_args = self.mock_client.invoke_model.call_args[1]
            self.assertEqual(call_args["prompt"], "Test prompt body")
            self.assertIn("system_prompt", call_args)

    def test_build_actionable_email(self):
        """Test building an actionable email"""
        with patch(
            "email_summarizer.utils.ai_utils.email_to_prompt"
        ) as mock_email_to_prompt:
            mock_email_to_prompt.return_value = {
                "prompt_body": "Test prompt body",
                "was_redacted": False,
            }

            actionable_email = build_actionable_email(self.mock_client, self.test_email)

            # Verify the actionable email was created correctly
            self.assertIsInstance(actionable_email, ActionableEmail)
            self.assertEqual(actionable_email.next_steps, "This is a test summary")
            self.assertEqual(actionable_email.email, self.test_email)

            # Verify the client was called correctly
            self.mock_client.invoke_model.assert_called_once()
            call_args = self.mock_client.invoke_model.call_args[1]
            self.assertEqual(call_args["prompt"], "Test prompt body")
            self.assertIn("system_prompt", call_args)

    def test_compile_email_report(self):
        """Test compiling an email report"""
        # Create test data
        emails = [self.test_email]
        grouped_emails = [GroupedEmails(sender="test@example.com", count=1)]
        high_priority_emails = [self.test_email]

        report = compile_email_report(
            self.mock_client,
            EmailAccounts.PRIMARY,
            emails,
            grouped_emails,
            high_priority_emails,
        )

        # Verify the report was created correctly
        self.assertIsInstance(report, EmailReport)
        self.assertEqual(report.email_account, EmailAccounts.PRIMARY)
        self.assertEqual(len(report.summaries), 1)
        self.assertEqual(len(report.actionable_emails), 1)
        self.assertEqual(len(report.grouped_emails), 1)
        self.assertIsInstance(report.timestamp, str)

        # Verify summaries were created
        self.assertIsInstance(report.summaries[0], Summary)
        self.assertEqual(report.summaries[0].email, self.test_email)

        # Verify actionable emails were created
        self.assertIsInstance(report.actionable_emails[0], ActionableEmail)
        self.assertEqual(report.actionable_emails[0].email, self.test_email)

        # Verify the client was called for both summaries and actionable emails
        self.assertEqual(self.mock_client.invoke_model.call_count, 2)

    def test_compile_email_report_empty(self):
        """Test compiling an email report with empty lists"""
        report = compile_email_report(
            self.mock_client, EmailAccounts.PRIMARY, [], [], []
        )

        # Verify the report was created correctly with empty lists
        self.assertIsInstance(report, EmailReport)
        self.assertEqual(report.email_account, EmailAccounts.PRIMARY)
        self.assertEqual(len(report.summaries), 0)
        self.assertEqual(len(report.actionable_emails), 0)
        self.assertEqual(len(report.grouped_emails), 0)
        self.assertIsInstance(report.timestamp, str)
        self.assertTrue(report.is_empty())

    def test_get_model_client(self):
        """Test getting the appropriate model client"""
        # Test Haiku model
        haiku_client = get_model_client(SupportedModel.CLAUDE_HAIKU)
        self.assertIsInstance(haiku_client, BedrockReasoningClient)
        self.assertEqual(haiku_client.default_model, AnthropicModels.HAIKU)

        # Test Sonnet model
        sonnet_client = get_model_client(SupportedModel.CLAUDE_SONNET)
        self.assertIsInstance(sonnet_client, BedrockReasoningClient)
        self.assertEqual(sonnet_client.default_model, AnthropicModels.SONNET)

        # Test unsupported model
        with self.assertRaises(ValueError) as context:
            get_model_client("unsupported_model")
        self.assertIn("Unsupported model", str(context.exception))
