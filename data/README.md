# Data and provenance

## HTTP observations

`results/benchmark-2026-09-12/attempts.jsonl` contains 600 records, one per measured HTTP attempt. All requests use a local server with authored fault schedules.

| Field | Definition |
|---|---|
| block | Consecutive collection block, 1 through 3 |
| sequence | Zero-based global request order |
| profile | Local service configuration, not a vendor |
| slot | Work-item identifier within a profile and block |
| planned_outcome | Configured fixture outcome |
| status | Observed HTTP status, or null if no status was received |
| usable | Whether the observed response satisfies the fixture payload contract |
| error | Actual failure category; null for a usable response |
| bytes | Complete body bytes read; zero for a timeout before receipt |
| elapsed_ns | Client elapsed time from before request through validation or error classification |
| usable_within_deadline | Usable and elapsed time no greater than 120 ms |

A timeout records time-to-abandonment, not an eventual server completion. The manifest stores the exact configuration, collection times, Python and OS versions, clock implementation, source SHA-256, and raw-data SHA-256. Error counts and percentiles use observed outcomes.

## Search-response fixtures

`evidence_cases.json` is an authored synthetic dataset. Its field names follow the documented SearchApi Google response shape, but no row was collected from the API. The example domains and instruction-like text are test material. The credential-bearing URL contains conspicuously dummy fixture values, not an account credential.

The mixed case contains 15 rows; six other cases exercise response-level states. Input indexes in the audit are zero-based. Original result positions are preserved as provided and are not used to reorder rows.

Every fixture candidate carries `content_kind=search_snippet`, `trust=untrusted`, and `claim_verified=false`. Null retrieval time means no retrieval took place. Candidate IDs hash normalized URLs; the snapshot hash supplies the version context.

## Regeneration

Reanalyzing retained benchmark observations reproduces the numeric aggregates exactly. Recollecting latency observations yields new timings. Replaying the authored fixtures reproduces their counts and normalized records deterministically.

The saved analyzer overwrites only derived summary/table files in the selected run directory. Collectors refuse existing output directories. Use a new directory when changing parameters or source code, and retain the matching manifest.
