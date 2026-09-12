# Source notes

Primary sources checked on 12 August 2026. These sources support design context and documented behaviour; experiment results come from this repository's retained data.

| Source | Used for |
|---|---|
| [SearchApi role](https://jobs.ashbyhq.com/searchapi/5202d0e3-e0c4-4a77-82e2-a8982f270de3) | Topic selection: reproducible benchmarks, technical writing, API tooling, and honest reporting |
| [SearchApi Google Search API](https://www.searchapi.io/docs/google) | Response field names, request context, and the saved-response adapter's scope |
| [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) | Distinguishing successful and failed request latency |
| [Python performance counter](https://docs.python.org/3/library/time.html#time.perf_counter_ns) | Elapsed-time measurement and integer nanosecond units |
| [Python URL parsing security](https://docs.python.org/3/library/urllib.parse.html#url-parsing-security) | Parsing versus input validation |

No third-party benchmark values or vendor performance claims are used. The documented SearchApi field names inform the adapter; the test payloads and their prose are original synthetic fixtures. No SearchApi subscription, key, or live API call was used in producing the published results.
