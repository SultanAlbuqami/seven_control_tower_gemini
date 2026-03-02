from __future__ import annotations

from src.utils.json_utils import extract_json


def test_extract_json_from_fenced_block():
    txt = """```json
    {"a": 1, "b": "x"}
    ```"""
    obj = extract_json(txt)
    assert obj is not None
    assert obj["a"] == 1


def test_extract_json_from_plain_text():
    txt = 'prefix {"k": [1,2,3]} suffix'
    obj = extract_json(txt)
    assert obj is not None
    assert obj["k"] == [1, 2, 3]
