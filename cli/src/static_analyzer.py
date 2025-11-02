# src/static_analyzer.py
import re
from pathlib import Path
from typing import List, Tuple, Dict

def read_code(path: Path) -> str:
    return path.read_text(encoding="utf-8")

"""Return list of checker ids which appear as exact tokens or appear in comments.


Heuristic search:
- look for occurrences of the checker id token (e.g. 'FNH.MIGHT')
- or simple rule-triggering keywords found in the KB text (we index first 6 words)


This is intentionally conservative — it returns a list of candidate checkers.
"""

def find_checker_mentions(code: str, kb: Dict[str, str]) -> List[str]:
    candidates = []
    code_lower = code.lower()
    
    # 1) exact tokens (e.g., comment `/* FNH.MIGHT */` or `// FNH.MIGHT`)
    for checker in kb.keys():
        if checker.lower() in code_lower:
            candidates.append(checker)


    # 2) keyword matching from KB short description (first 50 chars)
    # (optional, small contribution)
    for checker, text in kb.items():
        snippet = text.splitlines()[0][:200].strip().lower()
        tokens = re.findall(r"[a-z_]{3,}", snippet)
        for t in tokens[:6]:
            if t in code_lower and checker not in candidates:
                candidates.append(checker)
                break
    return candidates




"""Return simple map of line numbers to code for context display."""
def locate_functions_and_lines(code: str) -> Dict:
    lines = code.splitlines()
    return {i + 1: lines[i] for i in range(len(lines))}