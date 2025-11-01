import os
import json
import difflib
from datetime import datetime
from typing import Tuple, Dict

SUPPORTED_C_EXTENSIONS = [".c", ".h"]


def is_c_file(filepath: str) -> bool:
    """Return True if file is a valid C source/header file."""
    return os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() in SUPPORTED_C_EXTENSIONS


def read_file(filepath: str) -> str:
    """Read file and return contents as string."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_file(filepath: str, content: str) -> None:
    """Write content to file, creating directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def generate_unified_diff(original: str, modified: str, file_path: str) -> str:
    """Generate unified diff between original and modified content."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{file_path} (original)",
        tofile=f"{file_path} (modified)",
        lineterm=""
    )
    return "".join(diff)


def save_outputs(base_filename: str, modified_code: str, patch: str, metadata: Dict) -> Dict:
    """
    Save the modified code, patch, and JSON report to the outputs folder.
    Returns dict with saved file paths.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_dir = os.path.join("outputs", "raw")
    patch_dir = os.path.join("outputs", "patches")
    report_dir = os.path.join("outputs", "reports")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(patch_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    raw_filepath = os.path.join(raw_dir, f"{base_filename}_{timestamp}.c")
    patch_filepath = os.path.join(patch_dir, f"{base_filename}_{timestamp}.patch")
    report_filepath = os.path.join(report_dir, f"{base_filename}_{timestamp}.json")

    write_file(raw_filepath, modified_code)
    write_file(patch_filepath, patch)

    with open(report_filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    return {
        "raw_code_path": raw_filepath,
        "patch_path": patch_filepath,
        "report_path": report_filepath
    }
