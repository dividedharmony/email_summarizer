# Use an official AWS Lambda Python base image. Choose the Python version matching your project.
# Check for the latest available/recommended image tags: https://gallery.ecr.aws/lambda/python
ARG PYTHON_VERSION=3.12
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Set the working directory in the container
WORKDIR ${LAMBDA_TASK_ROOT}

# Install Poetry
# Using pipx is often recommended for tool installation
RUN pip install pipx && \
    pipx ensurepath && \
    pipx install poetry

# Assumes running as root, common in Docker builds. Adjust if using a different user.
ENV PATH="/root/.local/bin:${PATH}"

# Configure Poetry to not create virtual environments within the container
# This installs dependencies directly into the Python environment Lambda will use
RUN poetry config virtualenvs.create false

# Copy only the dependency definition files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install project dependencies (excluding development dependencies)
# Use --no-dev or --only main
RUN poetry install --only main --no-root

# Copy the rest of your application code
# Adjust the source path if your code is in a subdirectory like 'src/'
# Example if your code is in 'src/': COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY . ${LAMBDA_TASK_ROOT}/

# Set the PYTHONPATH to include the src directory
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/src:${PYTHONPATH}"

# Set the CMD to your handler function
# Format: <module_path>.<function_name>
# Example if your handler is in app.py: CMD [ "app.lambda_handler" ]
# Example if handler is in src/my_app/handler.py: CMD [ "src.my_app.handler.lambda_handler" ]
CMD [ "lambda_function.lambda_handler" ]
