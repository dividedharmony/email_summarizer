# Alphonse: the Email Summarizer

Alphonse is a Python application that automates email summarization and sharing. It reads emails from a Gmail account, uses AWS Bedrock's AI models to generate concise summaries, and posts these summaries to a Discord channel.

## Features

- Gmail integration for email reading
- AI-powered email summarization using AWS Bedrock
- Discord integration for sharing summaries
- Docker containerization for easy deployment
- Automated testing suite

## Prerequisites

- Python 3.9+
- Poetry for dependency management
- Docker
- AWS account with Bedrock access
- Gmail account with appropriate permissions
- Discord bot token and channel ID

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Then edit `.env` with your actual credentials and configuration values.

## Development

The project uses Poetry for dependency management. To activate the virtual environment:

```bash
poetry shell
```

## Testing

Run the test suite using:

```bash
poetry run poe test
```

The project uses Python's built-in `unittest` framework for testing. Tests are located in the `tests/` directory.

## Deployment

The application is containerized using Docker and deployed to AWS ECR (Elastic Container Registry). The deployment process is automated using the `deploy.sh` script.

To deploy:

```bash
./deploy.sh
```

This script handles:
- Building the Docker image
- Authenticating with AWS ECR
- Tagging and pushing the image to ECR

## Architecture

The application follows a modular architecture:
- Email reader module for Gmail integration
- Summarization module using AWS Bedrock
- Discord publisher module for sharing summaries
- Configuration management using environment variables

## Troubleshooting

Common issues and solutions:
1. Gmail authentication issues: Ensure you're using an App Password if 2FA is enabled
2. AWS Bedrock access: Verify your AWS credentials and Bedrock service access
3. Discord permissions: Check if the bot has proper permissions in the target channel

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
