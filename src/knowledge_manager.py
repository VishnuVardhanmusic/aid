import os
from typing import Optional


class KnowledgeManager:
    """
    Loads MISRA/Klocwork rule markdown files and provides rule context
    to be injected into the prompt for model-based code fixing.
    """

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.knowledge_base_dir = knowledge_base_dir

    def _get_rule_filepath(self, rule_name: str) -> str:
        """
        Returns the full path to the rule markdown file.
        Expected filename format: RULE_NAME.md  e.g., 'FNH.MIGHT.md'
        """
        return os.path.join(self.knowledge_base_dir, f"{rule_name}.md")

    def load_rule_full(self, rule_name: str) -> Optional[str]:
        """
        Load and return the full text of the rule markdown file.
        If not found, returns None.
        """
        filepath = self._get_rule_filepath(rule_name)

        if not os.path.isfile(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    # ------------------- FUTURE EXTENSIONS ------------------- #
    # These will be implemented later when S & C modes are added.

    def load_rule_summary(self, rule_name: str) -> Optional[str]:
        """
        TODO (for later S mode):
        Process the markdown and extract key parts:
        - Name + Summary
        - Vulnerability/Risk
        - Mitigation/Prevention
        - Short example
        """
        return None  # placeholder

    def load_rule_compressed(self, rule_name: str) -> Optional[str]:
        """
        TODO (for later C mode):
        Generate a compressed version suitable for low-token prompting.
        Instruction-only representation.
        """
        return None  # placeholder
