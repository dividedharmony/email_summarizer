import unittest
from ..base import BaseTestCase
from email_summarizer.utils.redaction_utils import redact_pii


class TestRedactionUtils(BaseTestCase):
    # Note: LICENSE_PLATE_REGEX is set in the .env.test file

    def test_redact_ssn(self):
        """Test redaction of Social Security Numbers."""
        test_cases = [
            "SSN: 123-45-6789",
            "SSN without dashes: 123456789",
            "Multiple SSNs: 123-45-6789 and 987-65-4321",
        ]
        for text in test_cases:
            result = redact_pii(text)
            self.assertTrue(result["was_redacted"])
            self.assertNotIn("123-45-6789", result["final_body"])
            self.assertNotIn("987-65-4321", result["final_body"])
            self.assertIn("<SSN>", result["final_body"])

    def test_redact_phone_number(self):
        """Test redaction of phone numbers."""
        test_cases = [
            "Phone: 123-456-7890",
            "Phone without dashes: 1234567890",
            "Phone with parentheses: (123) 456-7890",
            "Phone with parentheses and no space: (123)456-7890",
            "Multiple phones: 123-456-7890, (123) 456-7890, and 098-765-4321",
        ]
        for text in test_cases:
            result = redact_pii(text)
            self.assertTrue(result["was_redacted"])
            self.assertNotIn("123-456-7890", result["final_body"])
            self.assertNotIn("(123) 456-7890", result["final_body"])
            self.assertNotIn("098-765-4321", result["final_body"])
            self.assertIn("<PHONE_NUMBER>", result["final_body"])

    def test_redact_license_plate(self):
        """Test redaction of license plate numbers."""
        test_cases = [
            "License: ABC2468",
            "Multiple plates: ABC2468 and ABC-2468",
        ]
        for text in test_cases:
            result = redact_pii(text)
            self.assertTrue(result["was_redacted"])
            self.assertNotIn("ABC2468", result["final_body"])
            self.assertNotIn("ABC-2468", result["final_body"])
            self.assertIn("<LICENSE_PLATE>", result["final_body"])

    def test_multiple_pii_types(self):
        """Test redaction of multiple types of PII in one text."""
        text = "Contact: Phone 123-456-7890, SSN 123-45-6789, License ABC2468"
        result = redact_pii(text)

        self.assertTrue(result["was_redacted"])
        self.assertNotIn("123-456-7890", result["final_body"])
        self.assertNotIn("123-45-6789", result["final_body"])
        self.assertNotIn("ABC2468", result["final_body"])
        self.assertIn("<PHONE_NUMBER>", result["final_body"])
        self.assertIn("<SSN>", result["final_body"])
        self.assertIn("<LICENSE_PLATE>", result["final_body"])

    def test_no_pii(self):
        """Test text without any PII."""
        text = "This is a normal text without any personal information"  # No numbers or patterns that could match
        result = redact_pii(text)

        self.assertFalse(result["was_redacted"])
        self.assertEqual(text, result["final_body"])

    def test_empty_string(self):
        """Test redaction with empty string."""
        result = redact_pii("")

        self.assertFalse(result["was_redacted"])
        self.assertEqual("", result["final_body"])

    def test_non_string_input(self):
        """Test that non-string input raises AssertionError."""
        with self.assertRaises(AssertionError):
            redact_pii(None)
        with self.assertRaises(AssertionError):
            redact_pii(123)

    def test_preserve_surrounding_text(self):
        """Test that non-PII text is preserved."""
        text = "Before SSN 123-45-6789 After"
        result = redact_pii(text)

        self.assertTrue(result["was_redacted"])
        self.assertEqual("Before SSN <SSN> After", result["final_body"])


if __name__ == "__main__":
    unittest.main()
