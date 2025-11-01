### 📍 **Aider Based CLI Workflow**
In VSCode, you can build a Python-based CLI tool that uses **Aider as the AI code-modifier backend** to automatically fix MISRA/Klocwork violations inside C source files. Your Python CLI will accept a file or folder path as input, load the relevant MISRA rule content from your Knowledge Base `.md` files, then programmatically call **Aider** to generate code patches by passing the C code + rule context to the model. Aider will return a unified diff patch, which the CLI applies to update the code on disk. The output of the CLI will be the modified C files, a patch file, or a JSON report showing what was fixed. In this workflow: **Python acts as the orchestrator**, handling input, knowledge retrieval, and patch application; **Aider acts as the AI code-fixer engine**, and VSCode is simply your development environment to run, debug, and extend the CLI. Over time, you will automate more rules, bundle your CLI with configuration for model name, API key, base URL, and later integrate validation or test builds to confirm safe fixes.

### Project Structure

klocwork_ai_fixer/
│
├─ knowledge_base/              # your 253 MISRA .md files
│    ├─ FNH.MIGHT.md
│    ├─ ABV.ANY_SIZE_ARRAY.md
│    └─ ...253 files
│
├─ src/
│   ├─ __init__.py
│   ├─ cli.py                   # main entry point for CLI
│   ├─ aider_engine.py          # wrapper around Aider Library
│   ├─ rule_selector.py         # finds which MISRA rules apply to input code
│   ├─ report_generator.py      # builds JSON summary & patch file
│   ├─ file_utils.py            # read/write helpers
│   └─ config.py                # model name, base URL, api key
│
├─ outputs/
│   ├─ patches/                 # *.patch files go here
│   ├─ reports/                 # *.json reports go here
│   └─ modified/                # modified source files
│
├─ .env                         # for MODEL_NAME, API_KEY, API_BASE_URL
├─ requirements.txt
└─ README.md

(using Aider as a Python library)** gives us tighter integration and full control over inputs/outputs, which is important since you need 3 artifacts: modified files, patch file, and JSON report.

### **STEP 3: Implement `aider_engine.py`**

This file will:

* Initialize Aider’s Chat class with model credentials
* Load rule context
* Run Aider to generate code fixes
* Capture the diff/patch output

Before we proceed, **I need one clarification** so I write the correct Aider wrapper.

When Aider modifies code, how should the AI be instructed?

Choose one:

| Option                           | AI Fixing Style                                          | Example Behavior                          |
| -------------------------------- | -------------------------------------------------------- | ----------------------------------------- |
| **S (Strict MISRA Enforcement)** | Fix only when rule is violated; no optional improvements | Only MISRA corrections, no extras         |
| **I (Improvement Mode)**         | Fix MISRA + minor code quality issues                    | Cleans code while fixing MISRA            |
| **A (Advisor Mode)**             | Suggest fixes, but do not apply automatically            | AI outputs recommendations, user confirms |

For a **Klocwork Fixer Agent**, I recommend **S** (Strict Enforcement) to avoid altering valid code.

**Which fixing style should the engine default to?**
Reply with **S**, **I**, or **A**.

(If unsure, choose **S** — we can add flags later.)


## MODIFY FOLDER STRUCTURE
klocwork_ai_fixer/
│
├─ knowledge_base/               # 253 MISRA .md rule files
│    ├─ FNH.MIGHT.md
│    ├─ ABV.ANY_SIZE_ARRAY.md
│    └─ ...
│
├─ src/
│   ├─ __init__.py
│   ├─ cli.py                    # main entry point for CLI
│   ├─ aider_engine.py           # wrapper around Aider CLI / API
│   ├─ knowledge_manager.py      # loads rule context for prompts
│   ├─ rule_selector.py          # detects which rules apply
│   ├─ report_generator.py       # builds JSON summary & patch file
│   ├─ file_utils.py             # read/write helpers, diff creation
│   └─ config.py                 # config loader (env)
│
├─ outputs/
│   ├─ patches/                  # *.patch files
│   ├─ reports/                  # *.json reports
│   └─ raw/                      # modified source code (safe copy)
│
├─ .env                          # MODEL_NAME=..., API_KEY=...
├─ requirements.txt
└─ README.md

Before moving to **STEP 7: `rule_selector.py`**, one more **design decision** is needed:

## ❓ Rule Detection Mechanism Choice

When the CLI receives a `.c` file, how should we detect which MISRA/Klocwork rules apply?

Choose the approach for **v1 S-mode**:

| Code  | Method             | Description                                                                               | Effort  | Accuracy  |
| ----- | ------------------ | ----------------------------------------------------------------------------------------- | ------- | --------- |
| **T** | Tag-Based          | Detect rules if the file has comment tags like `/* FNH.MIGHT */` or `// MISRA: FNH.MIGHT` | Easiest | Medium    |
| **R** | Regex Matching     | Use regex per rule to detect patterns (e.g., division by iterator, void* cast, etc.)      | Medium  | Good      |
| **L** | LLM Classification | Ask LLM: “Which MISRA rules are violated in this code?”                                   | Medium  | Very High |
| **D** | Dual (R + L)       | Use regex as pre-filter, LLM to confirm                                                   | Higher  | **Best**  |

Recommendation: **D (Dual)**, to reduce token cost while keeping accuracy.

For the first working version, we can start with **T** (Tag-based) or **L** (LLM-based).

### 🧠 Since your test cases already include rule-name comments, I recommend **T** for initial POC**.

Please respond with one character: **T**, **R**, **L**, or **D**
(Default I will implement if you don’t choose: **T**)
