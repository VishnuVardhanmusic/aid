# src/kb_loader.py
from pathlib import Path
from typing import Dict
"""Load every markdown file under kb_dir. Return dict: {checker_name: content}.


Filenames are expected like `FNH.MIGHT.md` -> checker id `FNH.MIGHT`.
"""

def load_kb(kb_dir: Path) -> Dict[str, str]:
    kb = {}
    for p in sorted(kb_dir.glob("*.md")):
        name = p.stem # FNH.MIGHT from FNH.MIGHT.md
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            text = p.read_text(encoding="latin-1")
        kb[name] = text
    return kb