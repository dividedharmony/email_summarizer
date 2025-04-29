from unittest.mock import patch

from ..base import BaseTestCase
from email_summarizer.models.email import Email
from email_summarizer.utils.grouping_utils import (
    _build_grouping_categories,
    group_emails,
)


class TestGroupingUtils(BaseTestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create test emails
        self.warhorn_email = Email(
            id="warhorn-1",
            subject="Warhorn Event",
            sender="warhorn@example.com",
            date="2023-01-01T12:00:00Z",
            snippet="Warhorn event notification",
            body_preview="This is a Warhorn event notification.",
        )

        self.nextdoor_email = Email(
            id="nextdoor-1",
            subject="Nextdoor Alert",
            sender="nextdoor@example.com",
            date="2023-01-02T12:00:00Z",
            snippet="Nextdoor neighborhood alert",
            body_preview="This is a Nextdoor alert.",
        )

        self.spouse_email = Email(
            id="spouse-1",
            subject="From Spouse",
            sender="spouse@example.com",
            date="2023-01-03T12:00:00Z",
            snippet="Message from spouse",
            body_preview="This is a message from your spouse.",
        )

        self.daycare_email = Email(
            id="daycare-1",
            subject="Daycare Update",
            sender="daycare@example.com",
            date="2023-01-04T12:00:00Z",
            snippet="Daycare information",
            body_preview="This is a daycare update.",
        )

        self.ungrouped_email = Email(
            id="ungrouped-1",
            subject="Random Email",
            sender="random@example.com",
            date="2023-01-05T12:00:00Z",
            snippet="Random email",
            body_preview="This is a random email.",
        )

        # Set up environment variables for testing
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "SPOUSE_REGEX": r"spouse@example\.com",
                "DAYCARE_REGEX": r"daycare@example\.com",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()

    def test_build_grouping_categories(self):
        """Test building grouping categories"""
        categories = _build_grouping_categories()

        # Verify categories were created correctly
        self.assertEqual(len(categories), 4)

        # Check Warhorn category
        warhorn_category = next(cat for cat in categories if cat.name == "Warhorn")
        self.assertIsNotNone(warhorn_category)
        self.assertEqual(warhorn_category.count, 0)
        self.assertFalse(warhorn_category.high_priority)

        # Check Nextdoor category
        nextdoor_category = next(cat for cat in categories if cat.name == "Nextdoor")
        self.assertIsNotNone(nextdoor_category)
        self.assertEqual(nextdoor_category.count, 0)
        self.assertFalse(nextdoor_category.high_priority)

        # Check Spouse category
        spouse_category = next(cat for cat in categories if cat.name == "Spouse")
        self.assertIsNotNone(spouse_category)
        self.assertEqual(spouse_category.count, 0)
        self.assertTrue(spouse_category.high_priority)

        # Check Daycare category
        daycare_category = next(cat for cat in categories if cat.name == "Daycare")
        self.assertIsNotNone(daycare_category)
        self.assertEqual(daycare_category.count, 0)
        self.assertTrue(daycare_category.high_priority)

    def test_group_emails_all_categories(self):
        """Test grouping emails into all categories"""
        emails = [
            self.warhorn_email,
            self.nextdoor_email,
            self.spouse_email,
            self.daycare_email,
            self.ungrouped_email,
        ]

        result = group_emails(emails)

        # Verify the result structure
        self.assertIn("list_of_grouped_emails", result)
        self.assertIn("ungrouped_emails", result)
        self.assertIn("high_priority_emails", result)

        # Check grouped emails (non-high priority)
        self.assertEqual(len(result["list_of_grouped_emails"]), 2)
        warhorn_group = next(
            group
            for group in result["list_of_grouped_emails"]
            if "warhorn" in group.sender.lower()
        )
        self.assertEqual(warhorn_group.count, 1)
        nextdoor_group = next(
            group
            for group in result["list_of_grouped_emails"]
            if "nextdoor" in group.sender.lower()
        )
        self.assertEqual(nextdoor_group.count, 1)

        # Check high priority emails
        self.assertEqual(len(result["high_priority_emails"]), 2)
        self.assertIn(self.spouse_email, result["high_priority_emails"])
        self.assertIn(self.daycare_email, result["high_priority_emails"])

        # Check ungrouped emails
        self.assertEqual(len(result["ungrouped_emails"]), 1)
        self.assertIn(self.ungrouped_email, result["ungrouped_emails"])

    def test_group_emails_empty_list(self):
        """Test grouping an empty list of emails"""
        result = group_emails([])

        # Verify empty result structure
        self.assertEqual(len(result["list_of_grouped_emails"]), 0)
        self.assertEqual(len(result["ungrouped_emails"]), 0)
        self.assertEqual(len(result["high_priority_emails"]), 0)

    def test_group_emails_only_high_priority(self):
        """Test grouping only high priority emails"""
        emails = [self.spouse_email, self.daycare_email]

        result = group_emails(emails)

        # Verify high priority emails are captured
        self.assertEqual(len(result["high_priority_emails"]), 2)
        self.assertIn(self.spouse_email, result["high_priority_emails"])
        self.assertIn(self.daycare_email, result["high_priority_emails"])

        # Verify no regular grouped emails
        self.assertEqual(len(result["list_of_grouped_emails"]), 0)

        # Verify no ungrouped emails
        self.assertEqual(len(result["ungrouped_emails"]), 0)

    def test_group_emails_only_regular(self):
        """Test grouping only regular (non-high priority) emails"""
        emails = [self.warhorn_email, self.nextdoor_email]

        result = group_emails(emails)

        # Verify regular grouped emails
        self.assertEqual(len(result["list_of_grouped_emails"]), 2)
        warhorn_group = next(
            group
            for group in result["list_of_grouped_emails"]
            if "warhorn" in group.sender.lower()
        )
        self.assertEqual(warhorn_group.count, 1)
        nextdoor_group = next(
            group
            for group in result["list_of_grouped_emails"]
            if "nextdoor" in group.sender.lower()
        )
        self.assertEqual(nextdoor_group.count, 1)

        # Verify no high priority emails
        self.assertEqual(len(result["high_priority_emails"]), 0)

        # Verify no ungrouped emails
        self.assertEqual(len(result["ungrouped_emails"]), 0)

    def test_group_emails_only_ungrouped(self):
        """Test grouping only ungrouped emails"""
        emails = [self.ungrouped_email]

        result = group_emails(emails)

        # Verify ungrouped emails
        self.assertEqual(len(result["ungrouped_emails"]), 1)
        self.assertIn(self.ungrouped_email, result["ungrouped_emails"])

        # Verify no grouped emails
        self.assertEqual(len(result["list_of_grouped_emails"]), 0)

        # Verify no high priority emails
        self.assertEqual(len(result["high_priority_emails"]), 0)
