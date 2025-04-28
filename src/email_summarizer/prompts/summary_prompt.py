from email_summarizer.models.email import Email
from email_summarizer.prompts.pii_redaction import REDACTION_PROMPT
from email_summarizer.utils.email_utils import email_to_prompt

example_email = Email(
    id="1234567890",
    sender="Mellow Mushroom (mellowmushroom@example.com)",
    subject="Mellow Mushroom Order Received",
    date="12/31/2024",
    snippet="",
    body_preview="""
Order # 32146084855578624
(Note: You do not need this number to pickup)


Customer Name: Emily Jane
Customer Email: emilyjane@example.com
Customer Contact Number: 15551234567

* Payment Method: Credit Card Visa x-1234*
* ORDER FOR PICK UP *
Order ready at *8:46 PM*, TODAY (TUESDAY, 12/31/2024)

1 x Half & Half Pie
- 1 x Medium
- 1 x Regular Crust
- 1 x Customize Left
- 1 x Great White (1 x $10.50) =3D $10.50
- 1 x Customize Right
- 1 x Funky Q Chicken (1 x $11.50) =3D $11.50
SUBTOTAL $21.99
DIGITAL SERVICE FEE $0.49
TAX $1.85

*TOTAL*
* $24.33  *

Thank you for ordering online with Mellow Mushroom.
""",
)

SUMMARY_PROMPT = f"""
You are a helpful assistant that summarizes emails. You are given an email \
that includes the subject, sender, and body. Your task is to create a \
summary of the email.

# Email Intent
The intent of an email is the main purpose of the email. It is the reason \
the email was sent. All emails fall under one of the following categories:

| Intent | Description | Examples |
|--------|-------------|----------|
| TRANSACTION | The email confirms, updates, or completes a transaction with the sender. | Order confirmation, subscription reciepts, website's terms of service updates, etc. |
| SALE | The email is a sale or promotion from the sender to the recipient. This includes announcing a sale, a new product, a new service, etc. | A credit card company offering a new credit card, Amazon announcing a new product, etc. |
| SCHOOL | The email is about school or daycare related activity. Goddard is a daycare center. | Goddard announcing a new policy, a school announcing a new event, daycare asking parents to bring in diapers, etc. |
| REVIEW | The email is about a review of a product or service. | Amazon asking the customer to review their purchase, a hotel asking the customer to review their stay, etc. |
| INQUIRY | The email is direct request for more information from the sender to the recipient. | A financial advisor asking for a document, a doctor asking for a signature, etc. |
| ALERT | The email is a warning or alert. | A credit card company alerting the cardholder of a suspicious activity, Google alerting the user of a new sign in, etc. |
| SOCIAL | The email is a social media notification. Social media sites include Patreon, Facebook, Instagram, Twitter, etc. | A social media platform notifying the user of a new follower, Patreon notifying of a new 'Play to Win' post, etc. |
| OTHER | The email does not fall under any of the other categories. | A social media notification, a newsletter, a survey request, etc. |


# Summary Format
Summary should begin with the intent of the email. Then, summarize the email \
in a concise manner. The intent should be one word in all caps inside square \
brackets.


# Example Input
{email_to_prompt(example_email, disable_redaction=True)["prompt_body"]}

# Example Output
[TRANSACTION] Mellow Mushroom Order Received. Half & Half Pizza ready for pickup at 8:46 PM on 12/31/2024.

# Output Guidelines
- The summary should be concise and to the point.
- The summary should be in the present tense.
- The summary should be in the active voice.
- The summary should be no more than 100 words.
- Do not include your reasoning or any explanation of your response.
- Do not include any other text than the summary.
"""


def summary_system_prompt(needs_redaction: bool) -> str:
    if needs_redaction:
        return SUMMARY_PROMPT + "\n\n" + REDACTION_PROMPT
    return SUMMARY_PROMPT
