# src/llm_client.py
import os
from openai import OpenAI
from typing import Dict
from .config import MODEL_NAME

class LLMClient:
    def __init__(self, api_key: str = None, api_base: str = None, model: str = MODEL_NAME):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        api_base = api_base or os.environ.get("OPENAI_API_BASE")
        if api_key is None:
            raise ValueError("OPENAI_API_KEY (or API_KEY) environment variable must be set")
        kwargs = {"api_key": api_key}
        if api_base:
            kwargs["api_base"] = api_base
        self.client = OpenAI(**kwargs)
        self.model = model

"""Ask the model to produce a *fixed* version of the code.


The assistant should return the full updated source file only (no extra chatter).
We instruct the model to return the file in a fenced ```c block with a marker 'FIXED-CODE'.
"""

def propose_fix(self, checker_id: str, rule_text: str, filename: str, code: str) -> str:
    system = (
    "You are an assistant that helps fix C source code to comply with a MISRA-like rule. "
    "Given the rule text and the original source file, return a single fenced code block with the entire fixed source. "
    "If you cannot confidently fix, return the original file unchanged inside the fence and explain briefly outside the fence."
    )
    user_msg = (
    f"Checker: {checker_id}\n\nRule and guidance:\n{rule_text}\n\n"
    f"File: {filename}\n\nOriginal source:\n```c\n{code}\n```")


    resp = self.client.chat.completions.create(
    model=self.model,
    messages=[
    {"role": "system", "content": system},
    {"role": "user", "content": user_msg},
    ],
    max_tokens=1500,
    temperature=0.0,
    )
    # pick the assistant content
    content = resp.choices[0].message.content
    return content