# src/aider_engine.py
"""
AiderEngine - thin Python wrapper around the Aider CLI to behave like a library.
- Uses subprocess to call the `aider` CLI (documented scripting support).
- Uses git to capture unified-diff patches and list modified files.
- Designed to support three modes:
    S = Strict MISRA Enforcement  (fully implemented)
    I = Improvement Mode          (stubbed - minor optional changes)
    A = Advisor Mode             (stubbed - suggestions only)
Notes:
 - This wrapper expects the target project to be a git repo (we use git to capture diffs).
 - Aider tends to auto-commit changes; we snapshot the pre-run HEAD and diff against post-run HEAD.
 - For POC, the wrapper expects 'aider' to be available in PATH (installed via pip/pipx).
"""

import os
import shutil
import subprocess
import json
from typing import List, Dict, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).resolve().parents[1]
dotenv_path = project_root / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")

# Ensure outputs directories exist
OUTPUTS_DIR = project_root / "outputs"
PATCHES_DIR = OUTPUTS_DIR / "patches"
REPORTS_DIR = OUTPUTS_DIR / "reports"
MODIFIED_DIR = OUTPUTS_DIR / "modified"

for d in (OUTPUTS_DIR, PATCHES_DIR, REPORTS_DIR, MODIFIED_DIR):
    d.mkdir(parents=True, exist_ok=True)


class AiderEngineError(Exception):
    pass


class AiderEngine:
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize engine configuration; mostly passes through env settings.
        """
        self.model = model_name or MODEL_NAME
        self.api_key = api_key or API_KEY
        self.api_base = api_base or API_BASE_URL

        # NOTE: Aider CLI reads its own env vars or flags; we will set env for subprocess.
        self.env = os.environ.copy()
        if self.api_key:
            # Popular variables used by many providers; users may need to adjust if using other providers.
            self.env["OPENAI_API_KEY"] = self.api_key
            self.env["OPENAI_API_BASE"] = self.api_base or self.env.get("OPENAI_API_BASE", "")
            self.env["OPENAI_MODEL"] = self.model or self.env.get("OPENAI_MODEL", "")
            # Also set generic PROVIDER env names in case aider uses them (aider supports multiple backends)
            self.env["AIDER_API_KEY"] = self.api_key

    # -------------------------
    # Public API
    # -------------------------
    def run_strict_fix(self, file_paths: List[str], rule_md_text: str, rule_name: str) -> Dict:
        """
        Run Aider to strictly apply MISRA fix(es) to the given files.

        Parameters:
          file_paths: list of file paths (relative or absolute) that you want Aider to edit
          rule_md_text: the contents of the MISRA rule markdown (full text)
          rule_name: short name like 'FNH.MIGHT' used in reports

        Returns:
          A dictionary with keys:
            - modified_files: list of modified file paths (relative)
            - patch: unified diff string
            - summary: short textual summary
            - rule: rule_name
        """
        # Build the instruction message for Strict mode
        message = self._build_strict_message(rule_name, rule_md_text)

        return self._run_aider_and_collect(file_paths, message, mode="S", rule=rule_name)

    # stubs for other modes (I and A). These are intentionally minimal now.
    def run_improvement_mode(self, file_paths: List[str], rule_md_text: str, rule_name: str) -> Dict:
        """
        Improvement Mode (I) -- intended to allow Aider to make MISRA fixes + minor quality improvements.
        Currently a stub: uses the same prompt as strict for POC, but can be enhanced to relax constraints.
        """
        message = self._build_improvement_message(rule_name, rule_md_text)
        return self._run_aider_and_collect(file_paths, message, mode="I", rule=rule_name)

    def run_advisor_mode(self, file_paths: List[str], rule_md_text: str, rule_name: str) -> Dict:
        """
        Advisor Mode (A) -- intended to produce suggestions but NOT automatically apply changes.
        For POC this will instruct Aider to produce a patch and a textual explanation, but not apply changes.
        Implementation detail: because Aider's default behavior is to edit files, the "advisor" prompt asks for a patch
        in the response body (rather than editing files). We mark this as a TODO for future enhancement.
        """
        message = self._build_advisor_message(rule_name, rule_md_text)
        return self._run_aider_and_collect(file_paths, message, mode="A", rule=rule_name)

    # -------------------------
    # Internal helpers
    # -------------------------
    def _build_strict_message(self, rule_name: str, rule_md_text: str) -> str:
        """
        Compose a concise instruction for Aider to strictly fix MISRA violations.
        """
        instr = f"""Strict MISRA fix request for rule: {rule_name}

You are given the MISRA rule text below. Apply **only** the minimal code changes required to resolve the MISRA violation described.
- Do not change unrelated logic.
- Preserve function and variable names unless strictly necessary to fix the violation.
- Keep changes minimal and safe for compilation.
- If a test/validation step is required, add a small comment explaining how to validate (do not run tests).

MISRA Rule Text:
{rule_md_text}

Now modify the provided C source file(s) to strictly fix any occurrences of this rule.
Return edits by directly modifying files (Aider default behavior). When done, produce a short 1-2 sentence summary of changes for the JSON report.
"""
        return instr

    def _build_improvement_message(self, rule_name: str, rule_md_text: str) -> str:
        """
        Compose an instruction for the Improvement mode (I).
        (Currently a simple extension of strict message; can be tuned later)
        """
        instr = self._build_strict_message(rule_name, rule_md_text)
        instr += "\nIn addition to MISRA fixes, you may apply small improvements (formatting, small refactors) only if they help clarity."
        return instr

    def _build_advisor_message(self, rule_name: str, rule_md_text: str) -> str:
        """
        Compose an instruction for Advisor mode (A) — produce suggestions without modifying files.
        Note: Because aider CLI normally edits files, we'll ask Aider to produce a unified-diff in the chat,
        instead of editing. This behavior is best-effort for POC and may require future refinement.
        """
        instr = f"""Advisor mode: Inspect the file(s) and produce a unified-diff patch (text in your reply) that would fix `{rule_name}` occurrences.
Do NOT modify files automatically. Provide a short explanation for each hunk.
MISRA Rule Text:
{rule_md_text}
"""
        return instr

    def _run_aider_and_collect(self, file_paths: List[str], message: str, mode: str, rule: str) -> Dict:
        """
        Core flow:
         1. Ensure path list is non-empty
         2. Snapshot git HEAD
         3. Call: aider --message "<message>" <files...>
         4. After completion, capture git diff between old_head and new HEAD (or working tree)
         5. Build the result dict and return
        """
        if not file_paths:
            raise AiderEngineError("No files provided to AiderEngine._run_aider_and_collect")

        # normalize file paths
        file_paths = [str(Path(p)) for p in file_paths]

        # Ensure we are in a git repo (git rev-parse succeeds)
        # Use project_root as working dir for git commands
        wd = Path.cwd()
        if not (wd / ".git").exists():
            # If repo is not initialized, initialize a temporary git repo (safe for POC)
            # We will warn via printed message.
            print("[aider_engine] Warning: no .git found. Initializing temporary git repo for patch capture.")
            subprocess.run(["git", "init"], cwd=wd, check=True, env=self.env)
            subprocess.run(["git", "add", "."], cwd=wd, check=True, env=self.env)
            subprocess.run(["git", "commit", "-m", "initial commit (aider_engine snapshot)"], cwd=wd, check=True, env=self.env)

        # Snapshot HEAD
        old_head = self._git_rev_parse("HEAD")

        # Run aider CLI
        try:
            self._run_aider_cli(file_paths, message)
        except subprocess.CalledProcessError as e:
            # Capture aider stderr / stdout for debugging
            raise AiderEngineError(f"Aider CLI failed: {e}")

        # After Aider run, compute diff between old_head and new HEAD (if aider committed)
        # If aider committed, HEAD will have advanced. If not, there may be working-tree changes.
        new_head = self._git_rev_parse("HEAD")
        patch_text = ""
        modified_files = []

        if new_head != old_head:
            # There is a new commit(s). Get unified diff between old_head and new HEAD
            patch_text = self._git_diff(f"{old_head}..{new_head}")
            modified_files = self._git_diff_name_only(f"{old_head}..{new_head}")
        else:
            # No new commit. Show working tree diff vs old_head
            patch_text = self._git_diff(old_head)
            modified_files = self._git_diff_name_only(old_head)

        # Save patch file
        patch_filename = f"{rule.replace('/', '_')}_{Path(file_paths[0]).name}.patch"
        patch_path = PATCHES_DIR / patch_filename
        patch_path.write_text(patch_text, encoding="utf-8")

        # Optionally copy modified files to outputs/modified for snapshot
        for f in modified_files:
            src = Path(f)
            if src.exists():
                dest = MODIFIED_DIR / Path(f).name
                try:
                    shutil.copy2(src, dest)
                except Exception:
                    # non-fatal
                    pass

        # Short summary: list of files changed and number of hunks (approx)
        hunks = patch_text.count("\n@@ ") if patch_text else 0
        summary = f"Aider applied {len(modified_files)} modified files, {hunks} patch hunks."

        result = {
            "rule": rule,
            "mode": mode,
            "modified_files": modified_files,
            "patch": patch_text,
            "patch_file": str(patch_path),
            "summary": summary,
        }
        return result

    def _run_aider_cli(self, file_paths: List[str], message: str):
        """
        Invoke Aider CLI with message and files.
        Uses Aider's `--message` scripting option. We pass through model opts if present.
        """
        cmd = ["aider", "--message", message]
        # Optionally specify a model flag; only add if user wished a specific model
        # Many Aider installs accept `--model` and `--api-key` flags; we prefer env vars but expose them if present.
        if self.model:
            cmd += ["--model", self.model]
        # If the Aider install supports named API flags like 'anthropic' or 'openai', users can set them in env or pass.
        # Add target files
        cmd += file_paths

        # call aider - note: message may be large; for safety we pass it as an argument (aider supports --message)
        print(f"[aider_engine] Running: {' '.join(cmd[:3])} ... <{len(file_paths)} files>")
        subprocess.run(cmd, check=True, env=self.env)

    # -------------------------
    # Git helper wrappers
    # -------------------------
    def _git_rev_parse(self, ref: str) -> str:
        proc = subprocess.run(["git", "rev-parse", ref], capture_output=True, text=True, env=self.env)
        if proc.returncode != 0:
            raise AiderEngineError(f"git rev-parse failed: {proc.stderr.strip()}")
        return proc.stdout.strip()

    def _git_diff(self, ref_range: str) -> str:
        # ref_range can be 'old..new' or a single ref; produce unified diff
        proc = subprocess.run(["git", "diff", ref_range], capture_output=True, text=True, env=self.env)
        if proc.returncode not in (0, 1):  # git diff exits 1 for differences; treat 0/1 as ok
            raise AiderEngineError(f"git diff failed: {proc.stderr.strip()}")
        return proc.stdout

    def _git_diff_name_only(self, ref_range: str) -> List[str]:
        proc = subprocess.run(["git", "diff", "--name-only", ref_range], capture_output=True, text=True, env=self.env)
        if proc.returncode not in (0, 1):
            raise AiderEngineError(f"git diff --name-only failed: {proc.stderr.strip()}")
        names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return names


# For quick manual testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test AiderEngine")
    parser.add_argument("files", nargs="+", help="target C files to fix")
    parser.add_argument("--rule-file", required=True, help="path to MISRA rule .md (text)")
    parser.add_argument("--rule-name", required=True, help="rule name short id")
    args = parser.parse_args()

    rule_text = Path(args.rule_file).read_text(encoding="utf-8")
    engine = AiderEngine()
    result = engine.run_strict_fix(args.files, rule_text, args.rule_name)
    # write a JSON report file for quick inspection
    report_path = REPORTS_DIR / f"{args.rule_name}_{Path(args.files[0]).name}.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Report written to {report_path}")
    print(result["summary"])
