#!/bin/bash

# --- Configuration ---
AWS_ACCOUNT_ID="${ALPHONSE_ACCOUNT_ID}"

# Check if account id is empty
if [ -z "${AWS_ACCOUNT_ID}" ]; then
  # Print an error message to standard error (stderr)
  echo "Error: Environment variable ACCOUNT_ID_FROM_ENV is not set or is empty." >&2
  # Exit with a non-zero status (commonly 1 for general errors)
  exit 1
fi

AWS_REGION="us-east-1"
IMAGE_NAME="alphonse"
ECR_REPO_NAME="alphonse_v1"
IMAGE_TAG="v0.3.7"
FUNCTION_NAME="alphonse_email_summarizer"

# Construct ECR image URI
ECR_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"
LOCAL_IMAGE_TAG="${IMAGE_NAME}:${IMAGE_TAG}"

# --- Script Logic ---
set -e # Exit immediately if a command exits with a non-zero status.

echo "***** Building Docker image: ${LOCAL_IMAGE_TAG}"
docker build -t "${LOCAL_IMAGE_TAG}" .

echo "***** Tagging image for ECR: ${ECR_IMAGE_URI}"
docker tag "${LOCAL_IMAGE_TAG}" "${ECR_IMAGE_URI}"

echo "***** Authenticating Docker with ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "***** Pushing image to ECR: ${ECR_IMAGE_URI}"
docker push "${ECR_IMAGE_URI}"

echo "***** Updating Lambda function code: ${FUNCTION_NAME}"
aws lambda update-function-code \
    --function-name "${FUNCTION_NAME}" \
    --image-uri "${ECR_IMAGE_URI}" \
    --region "${AWS_REGION}"

echo "***** Deployment complete for ${FUNCTION_NAME} with image ${ECR_IMAGE_URI}"

# --- End of Script ---
