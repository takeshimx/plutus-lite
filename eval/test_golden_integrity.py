"""The golden set itself must stay consistent. These tests always run."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent


def test_expected_matches_dataset(tmp_path: Path) -> None:
    """expected.json must be exactly what make_expected.py computes from dataset.json."""
    spec = importlib.util.spec_from_file_location("make_expected", HERE / "golden" / "make_expected.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    data = json.loads((HERE / "golden" / "dataset.json").read_text(encoding="utf-8"))
    computed = {user: module.summarize(rows) for user, rows in data["users"].items()}
    stored = json.loads((HERE / "golden" / "expected.json").read_text(encoding="utf-8"))
    assert computed == stored


def test_reviewed_values_for_user_a_november() -> None:
    """Values approved at G5 (eval/README.md). Guards against changing dataset and expected together."""
    stored = json.loads((HERE / "golden" / "expected.json").read_text(encoding="utf-8"))
    nov = next(m for m in stored["user_a"]["monthly_summary"] if m["month"] == "2026-11")
    assert nov["income_total"] == 295000
    assert nov["expense_total"] == 16200
    assert nov["expense_by_category"] == [
        {"category": "日用品", "total": 8000},
        {"category": "食費", "total": 6200},
        {"category": "交通費", "total": 2000},
    ]


def test_dataset_keys_are_unique() -> None:
    data = json.loads((HERE / "golden" / "dataset.json").read_text(encoding="utf-8"))
    keys = [row["key"] for rows in data["users"].values() for row in rows]
    assert len(keys) == len(set(keys))
