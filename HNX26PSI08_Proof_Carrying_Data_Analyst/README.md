# HNX26PSI08 — Proof-Carrying Data Analyst

This is a ready-to-open VS Code starter project for the hackathon problem.

## What is included

- Streamlit dashboard
- CSV + Excel upload
- Data-quality checks
- Natural-language question analysis
- AI-generated pandas proof code
- Executed-code verification
- Automatic code repair (up to 3 attempts)
- Refusal/clarification path for unreliable questions
- Sample clean and messy datasets
- VS Code workspace file
- Windows one-click helper files

## Project structure

```text
HNX26PSI08_Proof_Carrying_Data_Analyst/
├── app.py
├── agent.py
├── code_generator.py
├── data_checker.py
├── verifier.py
├── prompts.py
├── requirements.txt
├── .env.example
├── HNX26PSI08.code-workspace
├── OPEN_PROJECT_IN_VSCODE.bat
├── run_windows.bat
├── .vscode/
│   └── extensions.json
└── sample_data/
    ├── sales.csv
    ├── customers.csv
    └── messy_sales.csv
```

## Easiest Windows setup

### Option A — open directly in VS Code

1. Extract the ZIP.
2. Double-click `OPEN_PROJECT_IN_VSCODE.bat`.
3. If the `code` command is not installed, open `HNX26PSI08.code-workspace` with VS Code.

### Option B — run the application

Double-click `run_windows.bat`. It will create a virtual environment, install packages, and start Streamlit.

## Manual setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your OpenAI API key in `.env`.

Then:

```bash
streamlit run app.py
```

## First test

Upload:

- `sample_data/sales.csv`

Ask:

> What is the total laptop sales?

The app generates code, executes it, and shows the verified result.

## Messy-data test

Upload:

- `sample_data/messy_sales.csv`

It intentionally contains a duplicate transaction, a missing amount, a mixed currency, and mixed date formats. Use this file to demonstrate the challenge's traps.

## Important security note

Do not run unrestricted LLM-generated Python in a production system. A production solution should execute code inside a hardened sandbox/container with network disabled, filesystem blocked, CPU/memory/time limits, and stronger static validation.
