import json
from typing import List, Optional

from .config import get_model_name, get_api_key, get_api_base_url
from openai import OpenAI


class RuleSelector:
    """
    Uses an LLM to detect which MISRA/Klocwork rules a given C file violates.
    Returns a list of rule names (matching .md filenames in knowledge_base).
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=get_api_key(),
            base_url=get_api_base_url()
        )
        self.model = get_model_name()

    def detect_rules(self, code: str) -> List[str]:
        """
        Sends the code to the LLM asking for violated MISRA/Klocwork rules.
        Returns a list of rule identifiers. Example: ["FNH.MIGHT", "DBZ.ITERATOR"]
        """
        prompt = f"""
You are an expert in MISRA C:2012 Amendment 2 and Klocwork static analysis rules.

Analyze the following C code and identify which MISRA/Klocwork rule IDs are violated.
Return ONLY a JSON array of rule names. No explanation, no text outside JSON.

Example output:
["FNH.MIGHT", "MISRA.DEFINE.WRONGNAME.UNDERSCORE"]

C Code to analyze:
--------------------
{code}
--------------------

Respond only with JSON list of rule names.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        ai_response = response.choices[0].message.content.strip()

        # If model responds with non-JSON, try to recover
        try:
            rules = json.loads(ai_response)
        except Exception:
            # Fallback: extract rule-like patterns manually
            rules = self._extract_possible_rule_ids(ai_response)

        # Ensure they are unique and sorted
        return sorted(set(rules))

    def _extract_possible_rule_ids(self, text: str) -> List[str]:
        """
        Fallback heuristic: extract words resembling RULE.NAME formats.
        """
        import re
        pattern = r"[A-Z0-9]+\.[A-Z0-9_.]+"
        return re.findall(pattern, text)
