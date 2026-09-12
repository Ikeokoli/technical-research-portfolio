# Technical research portfolio

Two technical articles with executable Python, retained inputs, measured outputs, and explicit limits.

| Read the article | Inspect the evidence |
|---|---|
| [When a faster API delivers fewer useful results](articles/01-api-benchmarks-that-count-failures.md) | [600 measured HTTP attempts](results/benchmark-2026-09-12/attempts.jsonl) · [runner](src/benchmark.py) · [analysis](src/analyze.py) |
| [From search results to traceable evidence](articles/02-search-results-to-traceable-evidence.md) | [authored fixtures](data/evidence_cases.json) · [adapter](src/evidence.py) · [row-level audit](results/evidence-2026-09-12/candidates.json) |

**Author portfolio:** [Ikechukwu Charles Okoli](https://github.com/Ikeokoli). Created 12 September 2026.

## Findings you can reproduce

- **API measurement:** the local fast profile had a 6.35 ms usable-response median and an 80% useful-result rate at a 120 ms deadline. The steady profile had a 12.24 ms median and a 98% useful-result rate. At a tighter 10 ms deadline, the ranking reverses.
- **Evidence handling:** the mixed 15-row fixture becomes six candidates, two duplicate occurrences, and seven rejected rows. Each input row has an audit entry.

The first is a controlled experiment with real loopback HTTP timings and intentionally injected faults. The second uses explicitly synthetic, authored search-response fixtures. **Neither is a live SearchApi benchmark, a provider comparison, or an evaluation of model accuracy.**

## Run locally

Python 3.10 or later; standard library only. The published run used Python 3.12.14. No API keys, paid services, package installation, or internet access are required after downloading the repository.

```bash
git clone https://github.com/Ikeokoli/technical-research-portfolio.git
cd technical-research-portfolio
python -m unittest discover -s tests -v
python src/analyze.py results/benchmark-2026-09-12
python src/fixture_audit.py --out results/local-evidence
```

On systems where Python is named `python3` or `py`, substitute that command. Every command runs from the repository root.

To make new latency measurements:

```bash
python src/benchmark.py --out results/local-benchmark
python src/analyze.py results/local-benchmark
```

The benchmark starts and stops its own loopback server. Your OS must allow local sockets. The collector and fixture replay require a new output directory, so previous observations cannot be silently replaced. Timings vary by machine and host activity; on a heavily loaded host, deadline outcomes can also vary.

For an already saved real response:

```bash
python src/normalize_snapshot.py work/response.json --out work/candidates.json
```

This command is offline and does not collect data from SearchApi.

## Evidence map

- [Benchmark manifest](results/benchmark-2026-09-12/manifest.json): environment, timing boundaries, configuration, source hash, and raw-data hash.
- [Benchmark summary](results/benchmark-2026-09-12/summary.json): pooled metrics, individual blocks, and deadline sensitivity.
- [Fixture summary](results/evidence-2026-09-12/summary.json): data classification, checksum, and disposition counts.
- [Data dictionary](data/README.md): definitions of retained fields.
- [Validation record](VALIDATION.md): checks executed before publication.
- [Source notes](SOURCES.md): primary documentation and the role that informed topic selection.

## Editorial and research provenance

These are newly prepared, AI-assisted portfolio samples. AI assisted with drafting, implementation, and review; the scripts were executed and the reported results checked against retained outputs. They do not claim prior publication, unaided authorship, production deployment, or hands-on evaluation of untested third-party tools.

The articles are tailored to the [SearchApi Technical Researcher / Writer role](https://jobs.ashbyhq.com/searchapi/5202d0e3-e0c4-4a77-82e2-a8982f270de3). The repository keeps the distinction between implemented behavior, measured observations, and proposed extensions visible.
