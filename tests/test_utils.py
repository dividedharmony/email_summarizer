from email_summarizer.models.email import Email


def mock_email(
    subject: str = "Test Email",
    sender: str = "test@example.com",
    body: str = "This is the body of the test email.",
) -> Email:
    return Email(
        id="123456789",
        subject=subject,
        sender=sender,
        date="2021-01-01",
        snippet="This is a test email.",
        body_preview=body,
    )
