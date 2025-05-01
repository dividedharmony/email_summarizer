from unittest.mock import patch, AsyncMock, Mock, call

from ..base import BaseAsyncTestCase
from ..test_utils import mock_email
from email_summarizer.controllers.alphonse_controller import (
    _report_header,
    _any_grouped_emails,
    put_email_report,
)
from email_summarizer.models.enums import EmailAccounts, SupportedModel
from email_summarizer.models.report import EmailReport
from email_summarizer.models.email import GroupedEmails
from email_summarizer.models.summary import Summary
from email_summarizer.models.actionable_email import ActionableEmail
from email_summarizer.utils.gmail_utils import EmailUnavailableError
import discord


class TestAlphonseController(BaseAsyncTestCase):
    def test_report_header(self):
        """Test that the report header is formatted correctly."""
        # Create a mock email report
        email_report = EmailReport(
            email_account=EmailAccounts.PRIMARY,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[],
        )

        # Call the function
        header = _report_header(email_report)

        # Assert the header is formatted correctly
        self.assertEqual(header, "# PRIMARY Email Report 2023-01-01")

    def test_any_grouped_emails_with_grouped_emails(self):
        """Test that _any_grouped_emails returns True when there are grouped emails."""
        # Create a mock email report with grouped emails
        grouped_email = GroupedEmails(sender="test@example.com", count=2)
        email_report = EmailReport(
            email_account=EmailAccounts.PRIMARY,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[grouped_email],
        )

        # Call the function
        result = _any_grouped_emails(email_report)

        # Assert the result is True
        self.assertTrue(result)

    def test_any_grouped_emails_without_grouped_emails(self):
        """Test that _any_grouped_emails returns False when there are no grouped emails."""
        # Create a mock email report without grouped emails
        email_report = EmailReport(
            email_account=EmailAccounts.PRIMARY,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[],
        )

        # Call the function
        result = _any_grouped_emails(email_report)

        # Assert the result is False
        self.assertFalse(result)

    def test_any_grouped_emails_with_zero_count(self):
        """Test that _any_grouped_emails returns False when grouped emails have count of 0."""
        # Create a mock email report with grouped emails that have count of 0
        grouped_email = GroupedEmails(sender="test@example.com", count=0)
        email_report = EmailReport(
            email_account=EmailAccounts.PRIMARY,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[grouped_email],
        )

        # Call the function
        result = _any_grouped_emails(email_report)

        # Assert the result is False
        self.assertFalse(result)

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_channel_not_found(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_client.get_channel.return_value = None

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_client.close.assert_awaited_once()
        mock_get_emails.assert_not_called()
        mock_compile_email_report.assert_not_called()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_channel_success(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        mocked_email = mock_email(
            sender="test_2@example.com",
        )

        mock_get_emails.return_value = [
            mocked_email,
        ]

        mock_compile_email_report.return_value = EmailReport(
            email_account=email_account,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[Summary(email=mocked_email, body="AI summary of the email")],
            grouped_emails=[],
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_channel.send.assert_has_awaits(
            [
                call("# PRIMARY Email Report 2023-01-01"),
                call("*No high priority emails to report.*"),
                call("1. (test_2@example.com) AI summary of the email"),
                call("*No grouped emails to report.*"),
            ]
        )
        mock_client.close.assert_awaited_once()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_email_unavailable_error(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        # Simulate EmailUnavailableError
        mock_get_emails.side_effect = EmailUnavailableError(
            "Gmail service not available"
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_channel.send.assert_awaited_once_with(
            "Error: Gmail service not available."
        )
        mock_client.close.assert_awaited_once()
        mock_compile_email_report.assert_not_called()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_forbidden_error(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        # Simulate discord.errors.Forbidden
        mock_client.get_channel.side_effect = discord.errors.Forbidden(
            Mock(), "Missing Permissions"
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_client.close.assert_awaited_once()
        mock_get_emails.assert_not_called()
        mock_compile_email_report.assert_not_called()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_general_exception(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        # Simulate a general exception
        mock_get_emails.side_effect = Exception("Unexpected error")

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_client.close.assert_awaited_once()
        mock_compile_email_report.assert_not_called()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_empty_report(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        mock_get_emails.return_value = []

        # Create an empty report
        mock_compile_email_report.return_value = EmailReport(
            email_account=email_account,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[],
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_channel.send.assert_has_awaits(
            [
                call("# PRIMARY Email Report 2023-01-01"),
                call("*No emails to report.*"),
            ]
        )
        mock_client.close.assert_awaited_once()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_with_actionable_emails(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        mocked_email = mock_email(
            sender="test@example.com",
        )

        mock_get_emails.return_value = [
            mocked_email,
        ]

        # Create a report with actionable emails
        mock_compile_email_report.return_value = EmailReport(
            email_account=email_account,
            timestamp="2023-01-01",
            actionable_emails=[
                ActionableEmail(
                    email=mocked_email,
                    next_steps="Action required: Respond to this email",
                )
            ],
            summaries=[],
            grouped_emails=[],
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_channel.send.assert_has_awaits(
            [
                call("# PRIMARY Email Report 2023-01-01"),
                call("1. (test@example.com) Action required: Respond to this email"),
                call("*No regular emails to report.*"),
                call("*No grouped emails to report.*"),
            ]
        )
        mock_client.close.assert_awaited_once()

    @patch("email_summarizer.controllers.alphonse_controller.get_emails")
    @patch("email_summarizer.controllers.alphonse_controller.compile_email_report")
    async def test_put_email_report_with_grouped_emails(
        self, mock_compile_email_report, mock_get_emails
    ):
        # GIVEN
        mock_client = Mock()
        mock_client.user = Mock()
        mock_client.user.name = "TestBot"
        mock_client.user.id = "123456789"
        mock_client.close = AsyncMock()
        email_account = EmailAccounts.PRIMARY
        channel_str = "987654321"
        max_emails = 3
        target_model = SupportedModel.CLAUDE_HAIKU

        mock_channel = Mock()
        mock_client.get_channel.return_value = mock_channel
        mock_channel.send = AsyncMock()

        mock_get_emails.return_value = []

        # Create a report with grouped emails
        mock_compile_email_report.return_value = EmailReport(
            email_account=email_account,
            timestamp="2023-01-01",
            actionable_emails=[],
            summaries=[],
            grouped_emails=[
                GroupedEmails(sender="group1@example.com", count=3),
                GroupedEmails(sender="group2@example.com", count=2),
            ],
        )

        # WHEN
        await put_email_report(
            discord_client=mock_client,
            email_account=email_account,
            channel_str=channel_str,
            max_emails=max_emails,
            target_model=target_model,
        )

        # THEN
        mock_channel.send.assert_has_awaits(
            [
                call("# PRIMARY Email Report 2023-01-01"),
                call("*No high priority emails to report.*"),
                call("*No regular emails to report.*"),
                call("### Grouped Emails"),
                call("- (group1@example.com) - message count: 3"),
                call("- (group2@example.com) - message count: 2"),
            ]
        )
        mock_client.close.assert_awaited_once()
