# tests/base.py
import os
import unittest

from dotenv import load_dotenv


def load_test_environment():
    """Loads the .env.test file"""
    print("Attempting to load .env.test ...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, ".env.test")
    if load_dotenv(dotenv_path=env_path, override=True):
        print(f"Successfully loaded test environment from: {env_path}")
    else:
        print(f"Warning: Could not load test environment from {env_path}")


# Load immediately when this module is imported
load_test_environment()


class BaseTestCase(unittest.TestCase):
    pass


class BaseAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    pass
