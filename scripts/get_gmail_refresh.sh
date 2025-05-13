#!/bin/bash

# --- Configuration ---
# Scope for reading Gmail. Adjust if you need different permissions (e.g., send, modify).
# See: https://developers.google.com/gmail/api/auth/scopes
SCOPE="https://www.googleapis.com/auth/gmail.readonly"
# The Redirect URI you configured in Google Cloud Console
# Playground: REDIRECT_URI="https://developers.google.com/oauthplayground"
REDIRECT_URI="https://auth.davidharmon.io/landing.html"
# Google's OAuth 2.0 endpoints
AUTHORIZATION_URL="https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount"
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
# Check for Client ID from environment variable first, otherwise prompt
if [ -n "$ALPHONSE_GOOGLE_CLIENT_ID" ]; then
    CLIENT_ID="$ALPHONSE_GOOGLE_CLIENT_ID"
    echo "Using Client ID from ALPHONSE_GOOGLE_CLIENT_ID environment variable."
else
    read -p "Enter your Google Client ID: " CLIENT_ID
fi

# Check for Client Secret from environment variable first, otherwise prompt
if [ -n "$ALPHONSE_GOOGLE_CLIENT_SECRET" ]; then
    # Check if running in a non-interactive shell or if secrets shouldn't be echoed
    # Basic check: if stdout is a terminal. More robust checks exist if needed.
    if [ -t 1 ]; then
        echo "Using Client Secret from ALPHONSE_GOOGLE_CLIENT_SECRET environment variable."
    fi
    CLIENT_SECRET="$ALPHONSE_GOOGLE_CLIENT_SECRET"
else
    read -s -p "Enter your Google Client Secret: " CLIENT_SECRET
    echo # Add a newline after secret input for better formatting
fi

# --- Step 1: Generate Authorization URL ---
# URL encode the scope (safer for potentially complex scopes)
ENCODED_SCOPE=$(printf "%s" "$SCOPE" | jq -Rr @uri)
ENCODED_REDIRECT_URI=$(printf "%s" "$REDIRECT_URI" | jq -Rr @uri)

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

# ---- Updating the Lambda function ----

# --- Configuration ---
FUNCTION_NAME="alphonse_email_summarizer"
PRIMARY_PREFIX="PRIMARY"
ALTERNATE_PREFIX="ALTERNATE"
NOREPLY_PREFIX="NOREPLY"
GMAIL_ENV_VAR_SUFFIX="GMAIL_REFRESH_TOKEN"
AWS_REGION="us-east-1"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed." >&2
    echo "Please install and configure it (run 'aws configure')." >&2
    exit 1
fi

# --- User Prompt ---
echo "Which account configuration should the Lambda function '$FUNCTION_NAME' use?"
# -p: prompt string, -n 1: read only one character, -r: raw input (no backslash escapes)
read -p "(P)rimary, (A)lternate, or (N)oreply? " -n 1 -r user_choice
echo # Move to a new line after single character input

target_account=""

# Determine the new value based on input (case-insensitive)
case $user_choice in
    [Pp])
        target_account="$PRIMARY_PREFIX"
        echo "Selected: Primary ($target_account)"
        ;;
    [Aa])
        target_account="$ALTERNATE_PREFIX"
        echo "Selected: Alternate ($target_account)"
        ;;
    [Nn])
        target_account="$NOREPLY_PREFIX"
        echo "Selected: Noreply ($target_account)"
        ;;
    *)
        echo # Add a newline for clarity
        echo "Invalid selection: '$user_choice'. Exiting." >&2
        exit 1
        ;;
esac

env_var_name=$(printf "%s_%s" "$target_account" "$GMAIL_ENV_VAR_SUFFIX")

echo "Environment variable name: $env_var_name"

# --- AWS CLI Operations ---

# Construct AWS command prefix (handles optional profile/region)
AWS_CMD_PREFIX="aws"
[[ -n "$AWS_PROFILE" ]] && AWS_CMD_PREFIX+=" --profile $AWS_PROFILE"
[[ -n "$AWS_REGION" ]] && AWS_CMD_PREFIX+=" --region $AWS_REGION"
AWS_CMD_PREFIX+=" lambda"

echo "Fetching current environment variables for Lambda function '$FUNCTION_NAME'..."

# Get current environment variables JSON using AWS CLI and jq
# --query 'Environment.Variables' extracts only the Variables map
# --output json ensures the output is valid JSON
current_env_json=$($AWS_CMD_PREFIX get-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --query 'Environment.Variables' \
    --output json 2>&1) # Capture stderr as well

# Check for errors fetching config (e.g., function not found, permissions)
if [[ $? -ne 0 ]]; then
    echo "Error fetching Lambda configuration:" >&2
    echo "$current_env_json" >&2 # Print the error message from aws cli
    exit 1
fi

echo "Current variables JSON fetched."
# Uncomment the line below for debugging to see the fetched JSON
# echo "$current_env_json"

# Prepare updated environment variables JSON using jq
# This handles the case where Environment.Variables might be null or empty
# It correctly adds or updates the specific variable ($ENV_VAR_NAME)
# --arg passes shell variables securely into the jq script
if [[ "$current_env_json" == "null" ]] || [[ -z "$current_env_json" ]]; then
    echo "No existing environment variables found. Creating new set."
    # Create JSON from scratch if no variables exist
    updated_env_json=$(jq -n \
        --arg key "$env_var_name" \
        --arg value "$REFRESH_TOKEN" \
        '{($key): $value}')
else
    echo "Updating existing environment variables."
    # Update the specific key in the existing JSON
    updated_env_json=$(echo "$current_env_json" | jq \
        --arg key "$env_var_name" \
        --arg value "$REFRESH_TOKEN" \
        '.[$key] = $value')
fi

# Check for errors during jq processing
if [[ $? -ne 0 ]]; then
    echo "Error processing environment variables with jq." >&2
    exit 1
fi

environment_payload_json=$(jq -n --argjson vars_map "$updated_env_json" '{Variables: $vars_map}')

echo "Environment payload JSON:"
echo "$environment_payload_json"
echo

echo "Updating Lambda function '$FUNCTION_NAME' with new environment variable '$env_var_name=$REFRESH_TOKEN'..."
# Uncomment the line below for debugging to see the JSON being sent
# echo "Sending JSON: Variables=$updated_env_json"

# Update the function configuration using the modified JSON
# Pass the entire updated JSON object to the --environment parameter
update_output=$($AWS_CMD_PREFIX update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --environment "$environment_payload_json" 2>&1) # Capture stderr

# Check the exit status of the AWS CLI update command
if [[ $? -eq 0 ]]; then
    echo "Successfully updated environment variable '$env_var_name' for Lambda function '$FUNCTION_NAME'."
    echo "New value: '$REFRESH_TOKEN'"
    echo "Note: It might take a moment for the changes to fully propagate and be reflected in new function invocations."
else
    echo "Error updating Lambda function:" >&2
    echo "$update_output" >&2 # Print the error message from aws cli
    exit 1
fi

exit 0
