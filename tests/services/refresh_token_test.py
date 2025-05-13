import unittest
from unittest.mock import Mock
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError, GoogleAuthError
from email_summarizer.services.refresh_token import is_refresh_token_valid


class TestRefreshToken(unittest.TestCase):
    def setUp(self):
        self.mock_credentials = Mock(spec=Credentials)
        self.mock_credentials.token = None

    def test_valid_refresh_token(self):
        """Test when refresh token is valid and returns a new access token."""
        self.mock_credentials.token = "new_access_token"
        result = is_refresh_token_valid(self.mock_credentials)
        self.assertTrue(result)
        self.mock_credentials.refresh.assert_called_once()

    def test_invalid_refresh_token(self):
        """Test when refresh token is invalid or expired."""
        self.mock_credentials.refresh.side_effect = RefreshError("invalid_grant")
        result = is_refresh_token_valid(self.mock_credentials)
        self.assertFalse(result)
        self.mock_credentials.refresh.assert_called_once()

    def test_missing_credentials(self):
        """Test when credentials are None."""
        with self.assertRaises(ValueError):
            is_refresh_token_valid(None)

    def test_google_auth_error(self):
        """Test when a Google authentication error occurs."""
        self.mock_credentials.refresh.side_effect = GoogleAuthError(
            "client auth failed"
        )
        result = is_refresh_token_valid(self.mock_credentials)
        self.assertFalse(result)
        self.mock_credentials.refresh.assert_called_once()

    def test_unexpected_error(self):
        """Test when an unexpected error occurs."""
        self.mock_credentials.refresh.side_effect = Exception("Unexpected error")
        with self.assertRaises(Exception):
            is_refresh_token_valid(self.mock_credentials)
        self.mock_credentials.refresh.assert_called_once()

    def test_refresh_success_no_token(self):
        """Test when refresh succeeds but no token is returned."""
        self.mock_credentials.token = None
        result = is_refresh_token_valid(self.mock_credentials)
        self.assertFalse(result)
        self.mock_credentials.refresh.assert_called_once()
