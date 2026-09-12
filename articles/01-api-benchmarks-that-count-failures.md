# When a faster API delivers fewer useful results

*Ikechukwu Charles Okoli · Technical research portfolio · 12 September 2026*

A search API can finish quickly and still leave an application with nothing it can use. That distinction disappears easily in a comparison table: sort providers by median response time, highlight the smallest number, and call it a recommendation.

In the local experiment published with this article, one HTTP service profile returned usable responses with a **6.35 ms median**. A second took **12.24 ms**. Yet, with a 120 ms useful-result deadline, the first delivered a usable result on **80% of attempts**, against **98%** for the second.

Those are measurements of a deliberately controlled experiment. The services run on the same computer, their failure schedules are authored, and neither represents SearchApi or a competitor. The purpose is to expose how the definition of success changes a benchmark's conclusion. The code makes actual HTTP requests; the recorded timings are observations, rather than values copied from the configured delays.

[Read the complete runner](../src/benchmark.py), [inspect all 600 attempts](../results/benchmark-2026-09-12/attempts.jsonl), or [recompute the aggregates](../src/analyze.py).

## Start with the application contract

Suppose a research assistant needs at least one usable search result before it can proceed. A successful transport connection alone does not satisfy that requirement. Neither does a valid JSON object containing an empty array.

For this experiment, an attempt is useful when all of these conditions hold:

- The response has HTTP status 200.
- The JSON contains an `organic_results` list with at least one nonblank title and a link under the fixture domain.
- Receiving and validating that response takes no more than 120 ms.

The fixture-domain rule is deliberately narrow. It checks the small response format used by this experiment; it does not measure relevance, freshness, factual accuracy, or comprehensive URL validity. A production comparison needs a contract tied to the actual task.

The resulting metric is:

```text
useful-result rate =
    usable responses completed within the deadline
    / all attempted requests
```

Failures remain in the denominator. A timeout contributes an unsuccessful attempt even though the final server response is never observed.

The metric complements latency. Google's SRE guidance recommends separating successful and failed request latency because quickly returned errors can distort a combined figure. The experiment adds an application-level payload check and a deadline to that distinction. [Source: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/).

## Build a failure schedule before measuring

The runner exposes two profiles through a local threaded HTTP server. Every block contains 100 requests to each profile, with the following fixed composition:

| Configured outcome per 100 requests | Fast, fragile | Steady |
|---|---:|---:|
| Usable JSON response | 80 | 98 |
| HTTP 200 with an empty result list | 5 | 0 |
| HTTP 503 | 5 | 2 |
| Response delayed beyond the client timeout | 10 | 0 |

Ordinary responses have configured sleeps of 2 ms and 8 ms respectively. Timeout fixtures sleep for 300 ms; the client socket timeout is 150 ms. These are configuration values, not the published latency measurements.

The experiment runs three consecutive blocks. Within each block, the 200 work items are shuffled using a fixed seed. Interleaving the profiles reduces the risk that one profile gets all the early requests and the other gets all the later requests while the host is busier. It cannot remove host scheduling noise.

There is one active client request at a time, a new TCP connection for each attempt, and no retries. Five success-path warmups per profile run before measurement and are excluded from the raw dataset. Server handlers for requests that have timed out may briefly remain active.

These choices keep the experiment understandable. They also limit it: this is a client-observed latency demonstration, not a concurrency, throughput, or connection-pooling benchmark.

## Keep the stopwatch outside response validation

The timer begins before the client sends the request. It stops after the body has been read and checked, or an error has been classified. Connection cleanup follows the timing boundary.

The essential operation is:

```python
started = time.perf_counter_ns()
# Connect, request, receive, parse, and validate; or classify the failure.
elapsed_ns = time.perf_counter_ns() - started
```

Python's performance counter measures elapsed time, including waits. Its nanosecond variant returns integer units; that does not imply nanosecond measurement accuracy. [Source: Python time documentation](https://docs.python.org/3/library/time.html#time.perf_counter_ns).

Every attempt retains its profile, block, sequence, work-item slot, planned outcome, actual status, actual error classification, bytes read, elapsed nanoseconds, and deadline result. Keeping both planned and observed outcomes matters: a busy machine could cause a nominally successful fixture to time out. Analysis uses the observed result.

The client setting is a socket timeout, not a hard limit on the entire operation. Operating-system scheduling and the time spent across stages can push observed elapsed time beyond 150 ms. The application deadline is evaluated separately after an attempt ends.

## The result changes when failures stay visible

The recorded run used Python 3.12.14 on Windows 11. The [manifest](../results/benchmark-2026-09-12/manifest.json) includes the configuration, UTC timestamps, clock implementation, source hash, and raw-data checksum.

| Observed metric | Fast, fragile | Steady |
|---|---:|---:|
| Attempted requests | 300 | 300 |
| HTTP 200 responses | 255 | 294 |
| Usable responses | 240 | 294 |
| Usable responses within 120 ms | 240 | 294 |
| Useful-result rate | 80.0% | 98.0% |
| Usable-response median | 6.35 ms | 12.24 ms |
| Usable-response p95 | 28.78 ms | 35.44 ms |
| All-attempt completion p95 | 161.53 ms | 35.27 ms |

The 18 percentage point useful-result gap is `100 × (294 / 300 − 240 / 300)`. It is an observed confirmation of the designed failure schedules, not an estimate of a real provider's reliability.

There are two traps in the faster profile's numbers. First, counting all HTTP 200 responses as successful reports 85% instead of 80%, because 15 responses contain no usable result. Second, the usable-response p95 excludes the 30 timeouts entirely. That conditional percentile answers how fast usable responses were when they arrived, not how long every caller waited.

The all-attempt percentile includes recorded time-to-failure. A timeout duration is the time the client waited before abandoning the attempt; it is not the server's eventual completion time. Reporting it under an explicit label avoids inventing an unobserved latency.

The code uses the nearest-rank percentile: sort the observations and select index `ceil(p × n) − 1`. In particular, p95 is calculated from the pooled attempt observations. It is not an average of block p95 values.

## A tighter deadline reverses the ranking

A useful-result rate still depends on a choice: useful by when?

Re-evaluating the same raw observations at several deadlines gives:

| Deadline | Fast, fragile: useful attempts | Steady: useful attempts |
|---|---:|---:|
| 10 ms | 54.3% | 2.0% |
| 20 ms | 66.7% | 66.7% |
| 50 ms | 79.0% | 96.7% |
| 120 ms | 80.0% | 98.0% |

This is a retrospective sensitivity analysis; the 120 ms primary threshold is defined in the runner. At 10 ms, the profile with more failures delivers more on-time results. At 20 ms, they tie. For this workload, recommending one profile without specifying the application's deadline hides the tradeoff.

The timing variation is also visible across blocks. The steady profile's median rises from 11.14 ms in block one to 14.08 ms in block three. Three blocks collected within seconds on one host are not evidence of stability over days. The repository preserves that variation instead of presenting the pooled median as a permanent property.

## What this experiment cannot justify

The profiles were constructed to differ. Their success counts do not warrant a statistical claim about a population of production requests, so a binomial confidence interval would add a misleading appearance of inference. The local timings also exclude the public internet, DNS resolution, TLS, real search execution, account limits, and billing.

A vendor comparison would need a different collection phase: representative queries, matched locale and device settings, a declared cache policy, separate runs at realistic concurrency, and repeated collection at different times. Relevance and freshness need their own evaluation. Retries should be reported at both attempt and end-to-end operation level, including all delay and any billed attempts.

The useful part of this small rig is its accounting discipline. Keep every attempt, state what makes its output useful, and make the recommendation conditional on the user's deadline.

## Reproduce the number

From the repository root, with Python 3.10 or later and no third-party packages:

```bash
python src/analyze.py results/benchmark-2026-09-12
python -m unittest discover -s tests -v
```

The first command verifies the raw-data checksum and regenerates the saved summary and table. To collect a new local run, use a fresh output directory:

```bash
python src/benchmark.py --out results/local-benchmark
python src/analyze.py results/local-benchmark
```

**Two-sentence reproduction:** Clone this repository, then run `python src/analyze.py results/benchmark-2026-09-12` to recover the 80% and 98% useful-result rates from the retained 600 observations. To rerun the experiment itself, execute `python src/benchmark.py --out results/local-benchmark` followed by `python src/analyze.py results/local-benchmark`; new latency values, and potentially deadline outcomes on a slow host, will differ.
