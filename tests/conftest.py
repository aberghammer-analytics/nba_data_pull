import os
import sys
from unittest import mock

# Mock modules before they're imported anywhere
# This happens before test collection, dramatically improving speed
sys.modules["boto3"] = mock.MagicMock()
sys.modules["botocore"] = mock.MagicMock()

# Add dummy AWS credentials to prevent credential lookup
os.environ.update(
    {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        "BUCKET_NAME": "test-bucket",
    }
)

# Pre-mock the inventory utilities that might be imported
# during test collection
mock_utils = mock.MagicMock()
mock_utils.load_yaml_s3 = mock.MagicMock(return_value={})
mock_utils.update_s3_inventory = mock.MagicMock(return_value={})
mock_utils.get_season_list = mock.MagicMock(return_value=[])
mock_utils.process_seasons = mock.MagicMock(return_value=([], []))
sys.modules["nba_data_pull.inventory.inventory_utils"] = mock_utils

# Optional but helpful: Custom pytest hooks to debug import time


def pytest_collectstart(collector):
    """Log when collection starts"""
    if collector.name == "test_create_inventory.py":
        print(f"\nCollecting {collector.name}...")


def pytest_itemcollected(item):
    """Log each collected test"""
    if "test_create_inventory" in item.nodeid:
        print(f"Collected: {item.name}")


def pytest_collection_finish(session):
    """Log when collection finishes"""
    print("\nCollection complete!")
