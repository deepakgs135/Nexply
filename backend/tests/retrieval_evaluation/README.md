# Candidate retrieval evaluation

> **Evaluation status: preliminary.** The current local dataset binds each question to every memory in its expected section(s). Those labels are useful for a first section-routing smoke evaluation, but they are not fact-level relevance annotations and do not meet Phase 5's manual relevance-label acceptance criterion. Do not use the retrieval precision/recall values as a validated quality claim or tune the retriever from them.

The dataset is candidate-specific through opaque Qdrant memory IDs, but it stores no app ID, resume text, or answer text. `query_catalog.py` contains the human-written question, expected intent, section scope, and relevance rationale. `build_local_dataset.py` binds those reviewed section scopes to the selected candidate's current memory IDs; it reads only point IDs and section labels from Qdrant.

## Prepare and run

Install backend dependencies, then set `NEXPLY_APP_ID` in the local process environment to the signed-in candidate's app ID. Do not put the ID in the JSON dataset or commit it. If the profile is reindexed or changes, regenerate the ID labels and review the question scopes before treating the report as comparable.

```powershell
python -m tests.retrieval_evaluation.build_local_dataset
python -m tests.retrieval_evaluation.evaluate_retrieval --name baseline
```

The evaluator refuses to run when `NEXPLY_APP_ID` is missing, validates every expected ID against that candidate's Qdrant ownership, and never prints candidate IDs or memory text. Reports are written under `docs/retrieval_evaluation/reports/` as JSON and Markdown.

K defaults to 1, 3, 5, and 10. The live retriever fetches the unthresholded top 10 once per question; threshold sweeps then filter this ranked list. This is equivalent for the reported cutoffs because each cutoff is at most 10, and avoids repeating Ollama embedding calls. A separate mocked retriever test verifies the actual Qdrant `score_threshold` argument is passed through.

## Metrics

Precision@K divides relevant unique results by the unique results actually returned up to K. Recall@K divides relevant unique results by the complete unique annotated set. Duplicate result IDs are counted once at their first rank. MRR is reciprocal rank of the first relevant unique result, and Hit Rate@K is one if at least one relevant result appears in the first K. Empty results, no relevant IDs, and failed requests produce safe zero-valued ranking metrics. Reports also include intent accuracy, section accuracy, empty-result rate, error rate, and mean query latency. Category-level and overall values are macro averages across questions.

## Annotation policy

Questions asking for every item in one or more sections currently mark every memory node in those requested sections relevant. This broad-coverage dataset measures section selection, not fact-level relevance, and can inflate or distort ranking metrics. The JSON includes no candidate profile text. Before claiming validated retrieval quality, replace these labels with manually reviewed individual memory IDs for each query and rationale. Do not use whole-section labels for narrow factual questions.

## Tests

Run mocked evaluation tests with:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q tests/retrieval_evaluation
```

These tests do not connect to MongoDB, PostgreSQL, Ollama, or Qdrant. The optional `test_live_retrieval.py` smoke test requires `NEXPLY_RUN_LIVE_RETRIEVAL=1` and a configured `NEXPLY_APP_ID`.
