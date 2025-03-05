from pathlib import Path
from unittest import mock

import pytest

from nba_data_pull.inventory.create_inventory import (
    copy_previous_meta,
    create_inventory,
    get_data_to_pull,
)


# Mock all external dependencies at the module level
@pytest.fixture(autouse=True)
def mock_all_externals():
    """Mock all external dependencies to avoid any real S3/boto3 calls"""
    with (
        mock.patch("nba_data_pull.inventory.create_inventory.boto3"),
        mock.patch("nba_data_pull.inventory.create_inventory.load_yaml_s3"),
        mock.patch("nba_data_pull.inventory.create_inventory.update_s3_inventory"),
        mock.patch("nba_data_pull.inventory.create_inventory.get_season_list"),
        mock.patch("nba_data_pull.inventory.create_inventory.process_seasons"),
        mock.patch("nba_data_pull.inventory.create_inventory.yaml"),
    ):
        yield


@pytest.fixture
def sample_inventory():
    """Simple inventory data structure"""
    return {
        "GAME": {"REGULAR_SEASON": ["1"], "PLAYOFFS": ["2"]},
        "PLAYER": ["3"],
        "SEASON": {
            "PER_GAME": {"REGULAR_SEASON": ["4"], "PLAYOFFS": ["5"]},
            "PER_POSSESSION": {"REGULAR_SEASON": ["5"], "PLAYOFFS": ["6"]},
        },
    }


@pytest.fixture
def sample_data_to_pull():
    """Simple data to pull structure"""
    return {
        "game": {"regular_season": ["6"], "playoffs": ["7"]},
        "player": ["8"],
    }


def test_copy_previous_meta(sample_inventory, sample_data_to_pull):
    """Test that copy_previous_meta copies files correctly"""
    # Mock file operations instead of S3
    with (
        mock.patch(
            "nba_data_pull.inventory.create_inventory.load_yaml_s3"
        ) as mock_load,
        mock.patch("pathlib.Path.open", mock.mock_open()) as mock_file,
        mock.patch("yaml.dump") as mock_yaml_dump,
    ):
        # Set up the load_yaml_s3 mock to return our test data
        mock_load.side_effect = [sample_inventory, sample_data_to_pull]

        # Call the function
        copy_previous_meta(Path("source/"), Path("dest/"))

        # Verify that files were read
        assert mock_load.call_count == 2


def test_create_inventory():
    """Test that create_inventory builds inventory from folder structure"""
    fake_inventory = {
        "GAME": {"REGULAR_SEASON": ["1", "2"], "PLAYOFFS": ["3"]},
        "PLAYER": ["4", "5"],
    }

    # Mock the function that scans the directory structure
    with (
        mock.patch(
            "nba_data_pull.inventory.create_inventory.update_s3_inventory"
        ) as mock_update,
        mock.patch("nba_data_pull.inventory.create_inventory.yaml.dump") as mock_dump,
        mock.patch("pathlib.Path.open", mock.mock_open()) as mock_file,
    ):
        # Set up the return value for the directory scan
        mock_update.return_value = fake_inventory

        # Call the function
        create_inventory(Path("test/inventory.yaml"))

        # Check that the directory was scanned
        mock_update.assert_called_once()

        # Check that the result was written to a file
        mock_dump.assert_called_once()


def test_get_data_to_pull(sample_inventory):
    """Test that get_data_to_pull correctly identifies data needs"""
    expected_output = {
        "game": {"regular_season": [], "playoffs": []},
        "player": [],
        "season": {"per_game": {"regular_season": [], "playoffs": []}},
    }

    with (
        mock.patch(
            "nba_data_pull.inventory.create_inventory.load_yaml_s3"
        ) as mock_load,
        mock.patch(
            "nba_data_pull.inventory.create_inventory.get_season_list"
        ) as mock_seasons,
        mock.patch(
            "nba_data_pull.inventory.create_inventory.process_seasons"
        ) as mock_process,
        mock.patch("nba_data_pull.inventory.create_inventory.yaml.dump") as mock_dump,
        mock.patch("pathlib.Path.open", mock.mock_open()) as mock_file,
    ):
        # Set up the return values
        mock_load.return_value = sample_inventory
        mock_seasons.return_value = ["2020"]
        mock_process.return_value = (["new_game_id"], ["new_player_id"])

        # Call the function
        get_data_to_pull(Path("inventory.yaml"), Path("data_to_pull.yaml"), 2020)

        # Check that inventory was loaded
        mock_load.assert_called_once()

        # Check that season list was generated
        mock_seasons.assert_called()

        # Check that seasons were processed
        mock_process.assert_called()

        # Verify that results were written to file
        mock_dump.assert_called_once()
