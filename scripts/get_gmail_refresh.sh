#!/bin/bash

# --- Configuration ---
# Scope for reading Gmail. Adjust if you need different permissions (e.g., send, modify).
# See: https://developers.google.com/gmail/api/auth/scopes
SCOPE="https://www.googleapis.com/auth/gmail.readonly"
# The Redirect URI you configured in Google Cloud Console
REDIRECT_URI="https://developers.google.com/oauthplayground"
# Google's OAuth 2.0 endpoints
AUTHORIZATION_URL="https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL="https://oauth2.googleapis.com/token"

# --- Check for jq ---
if ! command -v jq &> /dev/null
then
    echo "Error: 'jq' command not found."
    echo "Please install jq to parse JSON responses."
    echo "e.g., 'sudo apt install jq' or 'brew install jq'"
    exit 1
fi

# --- Get Credentials ---
read -p "Enter your Google Client ID: " CLIENT_ID

if [ -z "$CLIENT_ID" ]; then
  echo "Error: Client ID cannot be empty."
  exit 1
fi

read -s -p "Enter your Google Client Secret: " CLIENT_SECRET
echo # Add a newline after secret input

if [ -z "$CLIENT_SECRET" ]; then
  echo "Error: Client Secret cannot be empty."
  exit 1
fi

# --- Step 1: Generate Authorization URL ---
# URL encode the scope (safer for potentially complex scopes)
ENCODED_SCOPE=$(jq -sRr @uri <<< "$SCOPE")
ENCODED_REDIRECT_URI=$(jq -sRr @uri <<< "$REDIRECT_URI")

AUTH_URL_PARAMS="scope=$ENCODED_SCOPE&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri=$ENCODED_REDIRECT_URI&client_id=$CLIENT_ID&prompt=consent"
FULL_AUTH_URL="$AUTHORIZATION_URL?$AUTH_URL_PARAMS"

echo
echo "--- Step 1: Authorize Application ---"
echo "Visit the following URL in your web browser:"
echo
echo "$FULL_AUTH_URL"
echo
echo "1. Log in with the Google account you want the app to access."
echo "2. Grant the requested permissions (read Gmail)."
echo "3. You will be redirected to the OAuth 2.0 Playground."
echo "4. In the Playground (Step 2), click 'Exchange authorization code for tokens'."
echo "5. Copy the *Authorization code* that appears in the Playground interface or from the URL in your browser's address bar (the 'code' parameter)."
echo "   It will look something like: 4/0Af[...]Lwg"
echo

# --- Step 2: Get Authorization Code from User ---
read -p "Paste the Authorization Code here: " AUTHORIZATION_CODE

if [ -z "$AUTHORIZATION_CODE" ]; then
  echo "Error: Authorization Code cannot be empty."
  exit 1
fi

# --- Step 3: Exchange Authorization Code for Tokens ---
echo
echo "--- Step 3: Exchanging Code for Tokens ---"

# Use curl to post the request to the token endpoint
TOKEN_RESPONSE=$(curl --silent --show-error --location --request POST "$TOKEN_URL" \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode "code=$AUTHORIZATION_CODE" \
--data-urlencode "client_id=$CLIENT_ID" \
--data-urlencode "client_secret=$CLIENT_SECRET" \
--data-urlencode "redirect_uri=$REDIRECT_URI" \
--data-urlencode "grant_type=authorization_code")

# Check if curl command failed
if [ $? -ne 0 ]; then
    echo "Error: curl command failed to execute."
    echo "Check your network connection and the TOKEN_URL ($TOKEN_URL)."
    exit 1
fi

# Check if the response contains an error from Google
if echo "$TOKEN_RESPONSE" | jq -e '.error' > /dev/null; then
    echo "Error retrieving tokens from Google:"
    echo "$TOKEN_RESPONSE" | jq '.' # Print the error nicely formatted
    exit 1
fi

# --- Step 4: Extract and Display Refresh Token ---
REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.refresh_token')

echo
echo "--- Result ---"

if [ "$REFRESH_TOKEN" != "null" ] && [ -n "$REFRESH_TOKEN" ]; then
    echo "Successfully obtained Refresh Token!"
    echo "Store this securely in your application's configuration (e.g., AWS Secrets Manager or Parameter Store)."
    echo
    echo "Refresh Token: $REFRESH_TOKEN"
    echo
    # Optionally display the full response for debugging
    # echo "Full Token Response (JSON):"
    # echo "$TOKEN_RESPONSE" | jq '.'
else
    echo "Error: Could not extract Refresh Token from the response."
    echo "This might happen if:"
    echo " - You didn't request 'access_type=offline'."
    echo " - You didn't include 'prompt=consent' and have previously authorized this app without revoking access (Google might not issue a new refresh token)."
    echo " - The scope or other parameters were incorrect."
    echo
    echo "Full Token Response (JSON):"
    echo "$TOKEN_RESPONSE" | jq '.'
    exit 1
fi

exit 0
