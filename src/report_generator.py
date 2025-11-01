# src/report_generator.py
"""
Report Generation Helpers

This module provides functions to generate:
  - Per-file JSON reports
  - A full aggregated JSON report (all files)

Although cli.py already writes these, this module exists to keep future expansion clean:
  - HTML report export
  - PDF export
  - Excel/CSV summary
  - GUI mode integration
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def save_per_file_report(report_path: Path, report_obj: Dict) -> None:
    """
    Saves a single file's report at the given path.

    Args:
        report_path: Full path including filename.json
        report_obj: Dict containing report info
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_obj, indent=2), encoding="utf-8")


def save_full_report(full_report_path: Path, results: List[Dict]) -> None:
    """
    Saves aggregated report for all processed files.

    Args:
        full_report_path: outputs/full_report.json
        results: List of per-file results
    """
    aggregated = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_files": len(results),
        "results": results,
    }

    full_report_path.parent.mkdir(parents=True, exist_ok=True)
    full_report_path.write_text(json.dumps(aggregated, indent=2), encoding="utf-8")
