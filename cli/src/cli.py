# src/cli.py
import argparse
from pathlib import Path
from rich.console import Console
from .config import KB_DIR, DEFAULT_PROMPT, MAX_RULES_TO_PROCESS
from .kb_loader import load_kb
from .static_analyzer import read_code, find_checker_mentions, locate_functions_and_lines
from .llm_client import LLMClient
from .utils import unified_diff
console = Console()

def main():
    parser = argparse.ArgumentParser(description="Klocwork MISRA Fixer - semi-auto CLI")
    parser.add_argument("file", help="Path to C source file to analyze and fix")
    parser.add_argument("--kb", help="Path to knowledge_base directory", default=str(KB_DIR))
    parser.add_argument("--model", help="Model name override")
    parser.add_argument("--auto-apply", action="store_true", help="Auto apply all fixes (dangerous)")
    args = parser.parse_args()
    kb_dir = Path(args.kb)
    if not kb_dir.exists():
        console.print(f"[red]Knowledge base directory not found: {kb_dir}[/red]")
        return
    kb = load_kb(kb_dir)
    console.print(f"Loaded {len(kb)} rules from {kb_dir}")
    source_path = Path(args.file)
    code = read_code(source_path)
    candidates = find_checker_mentions(code, kb)
    if not candidates:
        console.print("[yellow]No explicit checker ids found. Running fuzzy match...[/yellow]")
        candidates = find_checker_mentions(code, kb) 

    console.print(f"Found {len(candidates)} candidate checkers (showing up to {MAX_RULES_TO_PROCESS})")
    candidates = candidates[:MAX_RULES_TO_PROCESS]
    llm = LLMClient()
    current_code = code
    for checker in candidates:
        console.rule(f"Candidate: {checker}")
        rule_text = kb.get(checker, "(no rule text found)")
        console.print(rule_text.splitlines()[:6])
        # ask LLM to propose fix
        console.print("Asking LLM for a proposed fix...")
        reply = llm.propose_fix(checker, rule_text, source_path.name, current_code)
        # extract fenced code if present
        import re
        m = re.search(r"```(?:c|C)\n([\s\S]*?)\n```", reply)
        if m:
            fixed = m.group(1).strip() + "\n"
        else:
            # fallback: take entire reply as code
            fixed = reply
        diff_text = unified_diff(current_code, fixed, fromfile=source_path.name, tofile=source_path.name)
        if not diff_text.strip():
            console.print("[green]No changes proposed by the model for this checker.[/green]")
            continue
        console.print(diff_text)
        if args.auto_apply:
            apply = True
        else:
            apply = console.input("Apply this change? (y/N): ").strip().lower() in ("y", "yes")
        if apply:
            current_code = fixed
            console.print("[green]Applied change.[/green]")
        else:
            console.print("[yellow]Skipped.[/yellow]")

    # at the end write out a new file
    out_path = source_path.with_suffix(source_path.suffix + ".fixed.c")
    out_path.write_text(current_code, encoding="utf-8")
    console.print(f"[bold]Final file saved to:[/bold] {out_path}")
        
if __name__ == '__main__':
    main()