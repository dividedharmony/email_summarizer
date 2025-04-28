from email_summarizer.models.email import Email


def email_to_prompt(email: Email) -> str:
    return f"""
    Sender: <sender>{email.sender}</sender>
    Subject: <subject>{email.subject} - {email.snippet}</subject>
    Body:
    <body>
        {email.body_preview}
    </body>
    """
