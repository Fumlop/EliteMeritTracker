import os
import json
import tempfile
import pytest
from load import load_json

def test_load_valid_json():
    # Create a temporary JSON file with required keys
    data = {"targets": [1, 2, 3]}
    required_keys = ["targets"]
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as tmp:
        json.dump(data, tmp)
        tmp_filepath = tmp.name

    loaded_data = load_json(tmp_filepath, required_keys)
    assert loaded_data == data
    os.remove(tmp_filepath)

def test_load_invalid_json():
    # Create a temporary file with invalid JSON content
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as tmp:
        tmp.write("invalid json")
        tmp_filepath = tmp.name

    loaded_data = load_json(tmp_filepath)
    assert loaded_data is None
    os.remove(tmp_filepath)

def test_missing_keys():
    # Create a temporary JSON file missing required keys
    data = {"values": [10, 20, 30]}
    required_keys = ["targets"]
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as tmp:
        json.dump(data, tmp)
        tmp_filepath = tmp.name

    loaded_data = load_json(tmp_filepath, required_keys)
    assert loaded_data is None
    os.remove(tmp_filepath)
