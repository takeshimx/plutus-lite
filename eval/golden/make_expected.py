"""Compute expected.json from dataset.json.

The expected values are reviewed by a human at G5. This script exists so the
numbers are not calculated by hand; it must not import application code.
Run: python eval/golden/make_expected.py
"""

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def summarize(rows: list[dict]) -> dict:
    months: dict[str, dict] = defaultdict(
        lambda: {"income_total": 0, "expense_total": 0, "categories": defaultdict(int)}
    )
    for r in rows:
        m = months[r["date"][:7]]
        if r["type"] == "income":
            m["income_total"] += r["amount_jpy"]
        else:
            m["expense_total"] += r["amount_jpy"]
            m["categories"][r["category"]] += r["amount_jpy"]

    summary = []
    for month in sorted(months, reverse=True):
        m = months[month]
        cats = sorted(m["categories"].items(), key=lambda kv: (-kv[1], kv[0]))
        summary.append(
            {
                "month": month,
                "income_total": m["income_total"],
                "expense_total": m["expense_total"],
                "expense_by_category": [{"category": c, "total": t} for c, t in cats],
            }
        )

    lists = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["date"], reverse=True):
        lists[r["date"][:7]].append(r["key"])

    return {
        "monthly_summary": summary,
        "list_by_month": {k: {"count": len(v), "keys_in_order": v} for k, v in lists.items()},
        "list_all_count": len(rows),
    }


def main() -> None:
    data = json.loads((HERE / "dataset.json").read_text(encoding="utf-8"))
    expected = {user: summarize(rows) for user, rows in data["users"].items()}
    (HERE / "expected.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
