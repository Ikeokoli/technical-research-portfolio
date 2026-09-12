"""Recompute every aggregate from retained attempt-level observations."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def percentile(values, fraction):
    """Nearest rank: sorted(values)[ceil(fraction * n) - 1]."""
    if not values:
        return None
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    return sorted(values)[math.ceil(fraction * len(values)) - 1]


def summarize(rows):
    result = {}
    for profile in sorted({r["profile"] for r in rows}):
        group = [r for r in rows if r["profile"] == profile]
        usable = [r for r in group if r["usable"]]
        latency = [r["elapsed_ns"] / 1e6 for r in usable]
        good = sum(r["usable_within_deadline"] for r in group)
        result[profile] = {
            "attempts": len(group), "http_200": sum(r["status"] == 200 for r in group),
            "usable": len(usable), "usable_within_deadline": good,
            "useful_result_rate_pct": 100 * good / len(group),
            "usable_p50_ms": percentile(latency, .50),
            "usable_p95_ms": percentile(latency, .95),
            "usable_p99_ms": percentile(latency, .99),
            "all_attempt_p95_ms": percentile([r["elapsed_ns"] / 1e6 for r in group], .95),
            "outcomes": dict(Counter(r["error"] or "usable" for r in group)),
            "deadline_sweep_pct": {str(limit): 100 * sum(
                r["usable"] and r["elapsed_ns"] <= limit * 1e6 for r in group
            ) / len(group) for limit in [10, 20, 50, 120]},
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    raw = (args.run / "attempts.jsonl").read_bytes()
    manifest = json.loads((args.run / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != manifest["raw_sha256"]:
        raise ValueError("Raw-data checksum does not match manifest")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    expected = manifest["blocks"] * len(manifest["profiles"]) * 100
    if len(rows) != expected:
        raise ValueError("Incomplete run")
    identities = {(r["block"], r["profile"], r["slot"]) for r in rows}
    expected_ids = {(b, p, s) for b in range(1, manifest["blocks"] + 1)
                    for p in manifest["profiles"] for s in range(100)}
    if identities != expected_ids:
        raise ValueError("Missing or duplicate work items")
    report = {"aggregate": summarize(rows), "by_block": {
        str(b): summarize([r for r in rows if r["block"] == b])
        for b in sorted({r["block"] for r in rows})}}
    (args.run / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    table = ["| Profile | Attempts | HTTP 200 | Usable | Useful by 120 ms | Usable p50 ms | Usable p95 ms | All-attempt p95 ms |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, r in report["aggregate"].items():
        def fmt(value):
            return "n/a" if value is None else f"{value:.2f}"
        table.append(f"| {name} | {r['attempts']} | {r['http_200']} | {r['usable']} | "
                     f"{r['useful_result_rate_pct']:.1f}% | {fmt(r['usable_p50_ms'])} | "
                     f"{fmt(r['usable_p95_ms'])} | {fmt(r['all_attempt_p95_ms'])} |")
    (args.run / "table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print("\n".join(table))


if __name__ == "__main__":
    main()
