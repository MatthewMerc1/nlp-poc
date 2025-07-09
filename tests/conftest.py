"""
Pytest configuration and shared fixtures for NLP POC tests.
"""

import pytest
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def sample_book_data():
    """Sample book data for testing."""
    return {
        'title': 'Test Book',
        'author': 'Test Author',
        'content': 'This is a test book content for testing purposes.',
        'book_id': 'test-book-1'
    }

@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    return [0.1] * 1536  # 1536-dimensional vector 