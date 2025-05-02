#!/bin/bash

FunctionName="alphonse_email_summarizer"
OutputFile="e2e/output.txt"
Region="us-east-1"

# --- Get Event File from Argument ---
if [ -z "$1" -o -z "$2" ]; then
  echo "Usage: $0 [account_type] [model]"
  echo "  account_type: primary, alt, or noreply"
  echo "  model: nova or haiku"
  exit 1
fi

ACCOUNT_TYPE_ARG="$1"
MODEL_ARG="$2"

# --- Determine Paths ---
# Get the absolute directory where the script resides, handling symlinks etc.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EVENT_FILE="${SCRIPT_DIR}/payload/${ACCOUNT_TYPE_ARG}_${MODEL_ARG}.json"

# --- Validate ---
if [ ! -f "$EVENT_FILE" ]; then
  echo "Error: Event file not found at $EVENT_FILE"
  exit 1
fi

echo "Using event file: $EVENT_FILE"
echo "Invoking function: $FunctionName"

aws lambda invoke \
    --function-name "$FunctionName" \
    --region "$Region" \
    --payload file://${EVENT_FILE} \
    --cli-binary-format raw-in-base64-out \
    "$OutputFile"

# --- Check Result ---
aws_exit_code=$?
if [ $aws_exit_code -eq 0 ]; then
  echo "Invocation successful. Output written to $OutputFile"
  echo "Function response:"
  cat "$OutputFile" # Optionally display the output
else
  echo "Error: AWS CLI invocation failed with exit code $aws_exit_code."
  # Note: The $OutputFile might still be created but empty or contain error info from Lambda itself.
  # Check stderr from the aws command or CloudWatch logs for details.
  exit 1
fi

echo # Add a newline for cleaner output

exit 0
