# Phase 5 retrieval evaluation — status and baseline

**Status: incomplete; baseline is preliminary.** The test framework and live baseline run are implemented, but the present dataset labels all memory nodes in each expected section as relevant. This does not satisfy the required per-query, manually verified, fact-level relevance annotation. Ranking metrics below are exploratory only and must not be presented as validated retrieval accuracy.

## Environment and execution

- Qdrant collection `candidate_memory_v1`: green, 65 points, 768-dimensional cosine vectors.
- Models: `qwen3.5:9b` for intent classification; `nomic-embed-text:latest` for query embeddings.
- Dataset: 40 questions across the required eight categories; no app ID or resume text is stored in the dataset or report.
- Live run: `python -m tests.retrieval_evaluation.evaluate_retrieval --name baseline`, against the selected candidate only. The runner validates every labeled point's owner and stores no memory payload text.
- Tests: full backend suite, 127 passed, 1 skipped; evaluation-specific suite, 32 passed, 1 skipped. One existing Starlette/httpx deprecation warning was reported by the full suite.

## Preliminary baseline results

Unthresholded top 10 was retrieved once per query, then cutoffs and thresholds were evaluated against that ranking. Thus latency is per query for classification plus retrieval and does not repeat for each threshold.

| Score threshold | Precision@5 | Recall@5 | MRR@5 | Hit@5 | Empty results | Intent / section accuracy | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| None | 0.905 | 0.641 | 0.931 | 0.975 | 0.0% | 92.5% / 92.5% | 29.27 s |
| 0.2 | 0.905 | 0.641 | 0.931 | 0.975 | 0.0% | 92.5% / 92.5% | 29.27 s |
| 0.4 | 0.880 | 0.624 | 0.906 | 0.950 | 2.5% | 92.5% / 92.5% | 29.27 s |
| 0.6 | 0.038 | 0.001 | 0.038 | 0.050 | 95.0% | 92.5% / 92.5% | 29.27 s |

These retrieval metrics use the preliminary section-wide relevance labels and are not reliable indicators of fact retrieval. The intent labels are independently authored and their accuracy is meaningful for this 40-query set, though the small set is not a production quality guarantee. General-profile intent accuracy was 60%; paraphrased/challenging intent accuracy was 75%.

## Findings and decisions

- A score threshold of `0.6` is plainly too strict in this run: it yielded a 95% empty-result rate. No threshold change was adopted.
- Threshold `0.2` exactly matched no threshold here; `0.4` was slightly worse on all reported top-5 metrics and had some empty results. Keep the existing unthresholded behavior until fact-level labels justify a change.
- General and paraphrased queries are the classifier's observed gaps. This dataset includes five general and four paraphrased queries, so treat these as leads for annotation and expanded testing, not conclusive error analysis.
- Mean end-to-end latency was about 29 seconds per query with local models. No classifier or retrieval tuning was adopted because this run did not establish an accuracy-preserving before/after result.
- Direct memory retrieval was evaluated. Hierarchical retrieval was not experimentally compared; no conclusion is claimed about whether it would improve results.
- No retrieval architecture, collection, index, or stored candidate data was changed. The Qdrant collection remains intact.

## Remaining acceptance work

1. Review candidate memory records privately and create fact-specific, manually verified query-to-memory-ID relevance labels. Keep IDs candidate-local and do not include profile text or identifiers in checked-in artifacts.
2. Rerun the baseline against those annotations; inspect misses using privacy-safe IDs and aggregate reason codes.
3. Compare direct retrieval with a hierarchical candidate → section → memory experiment using the same reviewed query labels.
4. Apply a retrieval/classifier change only when the reviewed benchmark demonstrates a problem, then rerun the same benchmark and publish before/after results.

Until those steps are complete, Phase 5 is not complete and the current baseline must be described as preliminary.
