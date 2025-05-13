import logging

from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Configure basic logging
LOG = logging.getLogger(__name__)


def is_refresh_token_valid(gmail_credentials: Credentials) -> bool:
    """
    Checks if a Google OAuth 2.0 refresh token is still valid by attempting
    to exchange it for a new access token using the google-auth library.

    Args:
        gmail_credentials: The credentials to validate.

    Returns:
        True if the refresh token is valid and a new access token can be obtained,
        False otherwise (specifically if a RefreshError indicating an invalid grant occurs).
        Raises GoogleAuthError for other authentication related issues or
        other exceptions for unexpected errors.
    """
    if not gmail_credentials:
        LOG.error("Gmail credentials must be provided.")
        raise ValueError("Gmail credentials must be provided.")

    try:
        LOG.info(
            "Attempting to refresh access token using google-auth to validate refresh token."
        )
        # Attempt to refresh the credentials.
        # A Request object is needed for the transport.
        gmail_credentials.refresh(Request())

        # If refresh() completes without an exception, and we have an access token,
        # the refresh token is considered valid.
        if gmail_credentials.token:
            LOG.info(
                "Refresh token is valid. New access token obtained via google-auth."
            )
            return True
        else:
            # This case should ideally not be reached if refresh() was successful
            # and didn't raise an error, but as a safeguard:
            LOG.warning(
                "Refresh token exchange via google-auth succeeded but no access token present."
            )
            return False

    except RefreshError as e:
        # This exception is raised when the refresh token is invalid, expired,
        # revoked, or the request is malformed (e.g., "invalid_grant").
        # The str(e) often contains the error reason like "invalid_grant".
        LOG.warning(
            "Refresh token is invalid or revoked (google.auth.exceptions.RefreshError): %s",
            e,
        )
        return False
    except GoogleAuthError as e:
        # Handles other Google authentication related errors (e.g., client auth failed)
        LOG.error("A Google authentication error occurred: %s", e)
        # Depending on the error, you might want to raise it or handle it differently.
        # For the purpose of this function, if we can't refresh, we consider it not valid for use.
        return False
    except Exception as e:
        # Catch any other unexpected errors during the process
        LOG.error(
            "An unexpected error occurred while validating refresh token with google-auth: %s",
            e,
        )
        raise  # Re-raise unexpected errors
