"""Aggregate evaluation records and write privacy-minimized JSON/Markdown reports."""

import json
from pathlib import Path

METRICS = ("precision", "recall", "mrr", "hit_rate")


def _average(rows: list[dict], field: str) -> float:
    return round(sum(row[field] for row in rows) / len(rows), 4) if rows else 0.0


def _score_rows(rows: list[dict], k_values: list[int]) -> dict:
    return {str(k): {metric: _average([{"value": row["metrics_at_k"][str(k)][metric]} for row in rows], "value")
                     for metric in METRICS} for k in k_values}


def _group_summary(rows: list[dict], k_values: list[int]) -> dict:
    return {"query_count": len(rows), "metrics_at_k": _score_rows(rows, k_values),
            "intent_accuracy": _average([{"value": float(row["actual_intent"] == row["expected_intent"])} for row in rows], "value"),
            "section_accuracy": _average([{"value": float(_section_correct(row))} for row in rows], "value"),
            "empty_result_rate": _average([{"value": float(row["result_count"] == 0)} for row in rows], "value"),
            "error_rate": _average([{"value": float(row["error_type"] is not None)} for row in rows], "value"),
            "average_latency_ms": _average(rows, "latency_ms")}


def _section_correct(row: dict) -> bool:
    if row["expected_intent"] == "GENERAL_SEARCH":
        return row["actual_source_section"] is None
    expected = row["expected_source_sections"]
    return len(expected) == 1 and row["actual_source_section"] == expected[0]


def summarize_results(queries: list[dict], rows_by_threshold: dict, k_values: list[int], thresholds: tuple) -> dict:
    """Produce overall and query-category macro averages for every threshold."""
    summaries = {}
    for threshold in thresholds:
        key = str(threshold)
        rows = rows_by_threshold[key]
        categories = {category: _group_summary([r for r in rows if r["category"] == category], k_values)
                      for category in sorted({q["category"] for q in queries})}
        summaries[key] = {"overall": _group_summary(rows, k_values), "by_category": categories,
                          "queries": rows}
    return {"query_count": len(queries), "k_values": k_values,
            "thresholds": list(thresholds), "runs_by_threshold": summaries}


def write_reports(report: dict, output_dir: Path, run_name: str, metadata: dict | None = None) -> tuple[Path, Path]:
    """Write machine-readable JSON and a concise human-readable summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"run_name": run_name, "metadata": metadata or {}, **report}
    json_path = output_dir / f"retrieval_{run_name}.json"
    md_path = output_dir / f"retrieval_{run_name}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(payload), encoding="utf-8")
    return json_path, md_path


def _markdown(report: dict) -> str:
    lines = [f"# Retrieval evaluation: {report['run_name']}", "", f"Queries: {report['query_count']}", ""]
    for threshold, result in report["runs_by_threshold"].items():
        overall = result["overall"]
        lines.extend([f"## Score threshold: {threshold}", "",
                      f"Intent accuracy: {overall['intent_accuracy']:.3f} · Section accuracy: {overall['section_accuracy']:.3f} · Empty results: {overall['empty_result_rate']:.3f}",
                      "", "| Category | Queries | P@K | R@K | MRR | Hit@K | Empty rate | Avg ms |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
        for category, values in result["by_category"].items():
            k = str(max(report["k_values"]))
            scores = values["metrics_at_k"][k]
            lines.append(f"| {category} | {values['query_count']} | {scores['precision']:.3f} | {scores['recall']:.3f} | {scores['mrr']:.3f} | {scores['hit_rate']:.3f} | {values['empty_result_rate']:.3f} | {values['average_latency_ms']:.1f} |")
        lines.append("")
    return "\n".join(lines)
