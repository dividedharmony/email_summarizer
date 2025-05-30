from email_summarizer.models.email import Email
from email_summarizer.prompts.pii_redaction import REDACTION_PROMPT
from email_summarizer.utils.email_utils import email_to_prompt

example_email = Email(
    id="1234567890",
    sender="Jane Doe (janedoe@example.com)",
    subject="Fwd: We've received your KFC order",
    date="12/31/2024",
    snippet="",
    body_preview="""
ORDER# 286529018

THANKS FOR YOUR ORDER

8:30 pm

We've received your order.

Quick Pick-up at KFC Chatham
123 West Alpha Blvd , Chatham, NC 55123

Meal for Two: 5 pc. Chicken Combo
5 pc. Chicken
2 Biscuits
Mashed Potatoes
Sweet Corn
Pepsi Zero Sugar
Pepsi Zero Sugar
$15.00

1

Honey Mustard
$0.20

1

Honey Sauce
FREE

1

Ketchup
FREE

Subtotal	$15.20
Tax	$1.25
Tips
Total	$16.45
""",
)

NEXT_STEPS_PROMPT = f"""
You are a helpful assistant that summarizes emails and determines the \
next steps. You are given an email that includes the subject, sender, \
and body. Your task is to create a summary of the email and determine \
the next steps the receipient should take.

# Output Format
The output should begin with the summary of the email in a concise manner. \
Then include the words "NEXT STEPS:" and describe the next immediate action \
the receipient should take.


## Possible Next Steps
Below is a table with descriptions of possible emails and the next step \
appropriate for that email. The list is not exhaustive. Feel free to \
suggest other next steps that are more appropriate for the given email.

| Description of Example Email | Example Next Step |
|---|---|
| Confirmation email of an upcoming flight, rental, event, etc | Add event details to calendar |
| Google drive folder is shared with recipient | Add appropriate files to shared folder |
| Confirmation email of restaurant order | Pick up order |
| Calendar invite to an upcoming event | Accept or decline event |
| Email from a friend or family member asking for a favor | Do the favor |
| Email asking a direct question | Respond to the question |
| Email asking to sign a document | Sign the document |
| Daycare asking for diapers | Buy diapers and drop off at daycare |
| School is informing about past school activities | Read full email |


# Example Input
{email_to_prompt(example_email, disable_redaction=True)["prompt_body"]}

# Example Output
Jane Doe forwarded an email from KFC. KFC received your order. \
NEXT STEPS: Pick up at 8:30 PM at 123 West Alpha Blvd, Chatham, NC 55123.

# Output Guidelines
- The summary should be concise and to the point.
- The summary should be in the present tense.
- The summary should be in the active voice.
- The summary should be no more than 100 words.
- Do not include your reasoning or any explanation of your response.
- Do not include any other text than the summary and the next steps.
- Next steps should be a single action that the recipient should take.
- Next steps should be actionable and specific.
"""


def next_steps_system_prompt(needs_redaction: bool) -> str:
    if needs_redaction:
        return NEXT_STEPS_PROMPT + "\n\n" + REDACTION_PROMPT
    return NEXT_STEPS_PROMPT
