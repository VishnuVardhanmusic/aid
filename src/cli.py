# src/cli.py
"""
klocfix - Minimal & Clean CLI (Python 3.10+)
-------------------------------------------
This is the minimal CLI entrypoint for the Klocwork AI Fixer POC (S mode implemented).

Usage examples (two styles):
  # After installing as a CLI entrypoint:
  klocfix fix ./src

  # Or during development without installing:
  python -m klocfix fix ./src

Commands:
  fix     <path>   : Detect MISRA rules and apply STRICT fixes (S mode). Produces:
                     - mirrored per-file modified files under outputs/modified/
                     - mirrored per-file patch files under outputs/patches/
                     - mirrored per-file JSON reports under outputs/reports/
                     - combined outputs/full_repo.patch (git-friendly unified diff)
                     - combined outputs/full_report.json (aggregated results)
  scan    <path>   : (stub) Detect violated rules only (no fixes). -- FUTURE (I mode)
  advisor <path>   : (stub) Provide suggestions only (no file edits). -- FUTURE (A mode)

Future-mode command examples (commented for reference):
  # Interactive mode (I) - prompt before apply:
  # klocfix fix ./src --mode i

  # Advisor mode (A) - generate patches/suggestions but don't edit files:
  # klocfix advisor ./src

Notes:
  - This minimal CLI expects the helper modules to exist:
      src/aider_engine.py       (AiderEngine)
      src/rule_selector.py     (RuleSelector)
      src/knowledge_manager.py (KnowledgeManager)
  - It auto-creates outputs/ folders if missing (per your preference).
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict

# Local imports (these modules are implemented in earlier steps)
from src.aider_engine import AiderEngine  # uses Aider CLI under the hood
from src.rule_selector import RuleSelector
from src.knowledge_manager import KnowledgeManager

# Constants for outputs
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODIFIED_DIR = OUTPUTS_DIR / "modified"
PATCHES_DIR = OUTPUTS_DIR / "patches"
REPORTS_DIR = OUTPUTS_DIR / "reports"
FULL_PATCH_PATH = OUTPUTS_DIR / "full_repo.patch"
FULL_REPORT_PATH = OUTPUTS_DIR / "full_report.json"

# Allowed C extensions (recursively scanned)
C_EXTS = {".c", ".h"}


def ensure_output_dirs() -> None:
    """Create outputs/ directory tree if absent."""
    for d in (OUTPUTS_DIR, MODIFIED_DIR, PATCHES_DIR, REPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def gather_source_files(path: Path) -> List[Path]:
    """
    Recursively collect .c/.h files under 'path'.
    If path is a file and a C file, returns [path].
    """
    paths: List[Path] = []
    if path.is_file():
        if path.suffix.lower() in C_EXTS:
            paths.append(path)
        return paths

    # directory: recursive glob
    for p in path.rglob("*"):
        if p.is_file() and p.suffix.lower() in C_EXTS:
            paths.append(p)
    return paths


def mirror_and_write_modified(src_file: Path) -> None:
    """
    Copy the current modified on-disk file (after Aider edit) to outputs/modified
    preserving relative tree under the working directory.
    """
    try:
        rel = src_file.relative_to(Path.cwd())
    except Exception:
        # fallback: use filename only
        rel = Path(src_file.name)

    dest = MODIFIED_DIR / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with src_file.open("rb") as fr, dest.open("wb") as fw:
            fw.write(fr.read())
    except Exception as e:
        print(f"[warn] could not copy modified file {src_file} -> {dest}: {e}")


def write_patch_for_file(rel_src: Path, patch_text: str) -> None:
    """Write a per-file patch into outputs/patches/<relative path>.patch"""
    dest = PATCHES_DIR / rel_src.with_suffix(rel_src.suffix + ".patch")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(patch_text or "", encoding="utf-8")


def write_report_for_file(rel_src: Path, report_obj: Dict) -> None:
    """Write JSON report for a single file under outputs/reports/<relative path>.json"""
    dest = REPORTS_DIR / rel_src.with_suffix(rel_src.suffix + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report_obj, indent=2), encoding="utf-8")


def aggregate_full_patch(per_file_patches: List[str]) -> None:
    """
    Create outputs/full_repo.patch by concatenating all per-file patches.
    Note: These patches are unified diffs; concatenation works for human review and
    'git apply' in many cases, but if exact ordering is required, use git to create a single diff.
    """
    combined = "\n\n".join([p for p in per_file_patches if p])
    FULL_PATCH_PATH.write_text(combined, encoding="utf-8")


def aggregate_full_report(results: List[Dict]) -> None:
    """Aggregate per-file results and write outputs/full_report.json"""
    full = {"generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z", "results": results}
    FULL_REPORT_PATH.write_text(json.dumps(full, indent=2), encoding="utf-8")


def run_fix(path: Path) -> None:
    """
    Main S-mode flow:
      - gather files
      - for each file: detect rules (LLM), for each rule load full rule md and call AiderEngine.run_strict_fix
      - collect results, write per-file patch + per-file report + copy modified file to outputs/modified
      - at end write full_repo.patch and full_report.json
    """
    ensure_output_dirs()

    # instantiate engine + helpers
    selector = RuleSelector()
    km = KnowledgeManager()
    engine = AiderEngine()

    src_files = gather_source_files(path)
    if not src_files:
        print(f"No C files found in {path}")
        return

    results: List[Dict] = []
    per_file_patches: List[str] = []

    for src in src_files:
        print(f"[scan] Analyzing {src}")
        code = src.read_text(encoding="utf-8")

        try:
            rule_ids = selector.detect_rules(code)
        except Exception as e:
            print(f"[error] rule detection failed for {src}: {e}")
            rule_ids = []

        if not rule_ids:
            print(f"[ok] No MISRA/Klocwork rules detected in {src}")
            continue

        # For S mode: apply strict fixes per detected rule (sequential)
        file_results: Dict = {"file": str(src), "rules": [], "file_patch": None}
        combined_patch_for_file = []

        for rule in rule_ids:
            rule_text = km.load_rule_full(rule)
            if not rule_text:
                print(f"[warn] rule '{rule}' not found in knowledge_base; skipping")
                file_results["rules"].append({"rule": rule, "status": "missing_rule_md"})
                continue

            try:
                print(f"[fix] Applying rule {rule} -> {src.name}")
                res = engine.run_strict_fix([str(src)], rule_text, rule)
            except Exception as e:
                print(f"[error] AiderEngine failed for {src} rule {rule}: {e}")
                file_results["rules"].append({"rule": rule, "status": "aider_failed", "error": str(e)})
                continue

            # res contains: modified_files, patch, patch_file, summary, rule, mode
            file_results["rules"].append(
                {"rule": rule, "status": "applied", "summary": res.get("summary", ""), "patch_file": res.get("patch_file")}
            )

            patch_text = res.get("patch", "")
            if patch_text:
                combined_patch_for_file.append(patch_text)
                per_file_patches.append(patch_text)

        # If Aider edited files in-place, copy modified file snapshot to outputs/modified (mirrored)
        mirror_and_write_modified(src)

        # Write per-file patch (combined patch of all hunks for that file)
        rel_src = src.relative_to(Path.cwd()) if src.is_relative_to(Path.cwd()) else Path(src.name)
        combined_patch_text = "\n\n".join(combined_patch_for_file)
        write_patch_for_file(rel_src, combined_patch_text)
        file_results["file_patch"] = str((PATCHES_DIR / rel_src.with_suffix(rel_src.suffix + ".patch")).resolve())

        # Write per-file JSON report
        write_report_for_file(rel_src, file_results)

        results.append(file_results)

    # After processing all files, generate aggregated artifacts
    aggregate_full_patch(per_file_patches)
    aggregate_full_report(results)

    print(f"\nDone. Aggregated patch: {FULL_PATCH_PATH}")
    print(f"Aggregated report: {FULL_REPORT_PATH}")
    print(f"Per-file outputs are under: {OUTPUTS_DIR}")


def run_scan(path: Path) -> None:
    """Scan-only command (stub). Will use rule_selector to detect rules and print them."""
    selector = RuleSelector()
    src_files = gather_source_files(path)
    for src in src_files:
        print(f"[scan] {src}")
        code = src.read_text(encoding="utf-8")
        try:
            rules = selector.detect_rules(code)
            print(json.dumps({"file": str(src), "rules": rules}, indent=2))
        except Exception as e:
            print(f"[error] scan failed for {src}: {e}")


def run_advisor(path: Path) -> None:
    """Advisor mode (stub). Intended to ask Aider to produce suggested patches but not write them.
    FUTURE: will call AiderEngine.run_advisor_mode and save suggestions to outputs/advisory/
    """
    print("[advisor] Advisor mode is a stub for now. Future behavior: produce suggestions but do not edit files.")
    # Example future flow:
    # 1) detect rules
    # 2) for each file/rule call engine.run_advisor_mode([...])
    # 3) collect advisor patches & explanations into outputs/advisory/


def main() -> None:
    parser = argparse.ArgumentParser(prog="klocfix", description="Klocwork AI Fixer (POC, S-mode).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_fix = sub.add_parser("fix", help="Detect and fix MISRA violations (S mode).")
    p_fix.add_argument("path", help="File or directory to fix", type=str)

    p_scan = sub.add_parser("scan", help="Scan only - list rules (no fixes) (stub).")
    p_scan.add_argument("path", help="File or directory to scan", type=str)

    p_adv = sub.add_parser("advisor", help="Advisor mode - suggestions only (stub).")
    p_adv.add_argument("path", help="File or directory to analyze", type=str)

    args = parser.parse_args()

    path = Path(args.path).resolve()
    if args.command == "fix":
        run_fix(path)
    elif args.command == "scan":
        run_scan(path)
    elif args.command == "advisor":
        run_advisor(path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
