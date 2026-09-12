# Validation record

Executed locally on 12 September 2026 with Python 3.12.14 on Windows 11.

| Check | Result |
|---|---|
| Unit tests | 10 passed |
| Fixture replay | 7 cases; all 14 state/count expectations passed |
| HTTP collection | 600 measured attempts across 3 consecutive blocks; 10 excluded warmups |
| Raw-data integrity | SHA-256 matched the benchmark manifest |
| Collection-source integrity | Current benchmark source SHA-256 matched the manifest |
| Headline counts and medians | Matched saved aggregate results |
| Saved-response command | Mixed fixture processed successfully into 6 candidates |
| Repository-relative article and README links | Checked for existing targets before publication |

## Scope of verification

The unit suite covers percentile calculation, retention of failures in denominators, payload validation, the fault schedule, URL equivalence boundaries, invalid URL inputs, internationalized and IPv6 hosts, missing versus empty responses, duplicate provenance, and untrusted snippet handling.

The benchmark completed without unplanned transport failures. Recorded failure categories matched the configured local fault schedule. The three blocks were collected during one short session on one host, not on different days.

No live SearchApi requests, external provider comparisons, model calls, production load tests, or measurements of token savings were performed. The saved-response command was exercised with an authored fixture. Re-running on a different machine is expected to change observed latencies.

## Commands executed

```bash
python -m unittest discover -s tests -v
python src/benchmark.py --out results/benchmark-2026-09-12
python src/analyze.py results/benchmark-2026-09-12
python src/fixture_audit.py --out results/evidence-2026-09-12
```

The published directories already exist. To collect or replay again, substitute a new directory beginning with `results/local-`. Re-analysis of existing benchmark data is supported.
