"""Replay authored fixtures, retaining normalized candidates and disposition counts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from evidence import adapt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("data/evidence_cases.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    raw = args.fixtures.read_bytes()
    fixtures = json.loads(raw)
    results = {case["id"]: adapt(case["payload"], {"source": "authored synthetic fixture",
               "fixture_id": case["id"], "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
               "query": "synthetic evidence adapter test", "retrieved_at": None})
               for case in fixtures["cases"]}
    checks = []
    for case in fixtures["cases"]:
        result = results[case["id"]]
        checks.append(result["state"] == case["expected_state"])
        if "expected_candidates" in case:
            checks.append(len(result["candidates"]) == case["expected_candidates"])
    if not all(checks):
        raise AssertionError("Fixture expectations failed")
    mixed = results["mixed_results"]
    summary = {"data_kind": fixtures["data_kind"], "fixture_sha256": hashlib.sha256(raw).hexdigest(),
               "case_count": len(results), "expectation_checks": len(checks), "checks_passed": sum(checks),
               "mixed_input_rows": len(fixtures["cases"][0]["payload"]["organic_results"]),
               "mixed_candidates": len(mixed["candidates"]),
               "mixed_dispositions": dict(Counter(r["action"] for r in mixed["audit"])),
               "mixed_rejection_reasons": dict(Counter(r["reason"] for r in mixed["audit"] if r["action"] == "reject"))}
    for name, data in [("candidates.json", results), ("summary.json", summary)]:
        (args.out / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
