import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import analyze_question, generate_code, repair_code
from data_checker import build_context, check_data_quality, _safe_name
from verifier import execute_code

load_dotenv()

st.set_page_config(
    page_title="Proof-Carrying Data Analyst",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Proof-Carrying Data Analyst")
st.caption("HNX26PSI08 • Agentic GenAI • Data Analytics • Code Generation • Verification")

with st.sidebar:
    st.header("Project Status")
    api_ready = bool(os.getenv("OPENAI_API_KEY"))
    st.write("OpenAI API:", "✅ Configured" if api_ready else "❌ Missing")
    st.info("Every numerical result displayed as an answer is obtained from executed Python code.")

files = st.file_uploader(
    "Upload CSV or Excel files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
)

if not files:
    st.info("Upload at least one CSV/Excel file to start.")
    st.markdown("### Try the included sample files")
    st.code("sample_data/sales.csv\nsample_data/customers.csv\nsample_data/messy_sales.csv")
    st.stop()

# -------------------- LOAD TABLES --------------------
dataframes = {}
file_errors = []

for uploaded in files:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        dataframes[f"{_safe_name(uploaded.name)}_df"] = df
    except Exception as exc:
        file_errors.append(f"{uploaded.name}: {exc}")

if file_errors:
    for err in file_errors:
        st.error(err)

if not dataframes:
    st.stop()

# -------------------- QUALITY --------------------
quality_reports = {}
st.header("1. Data Quality")

for variable_name, df in dataframes.items():
    report = check_data_quality(df)
    quality_reports[variable_name] = report

    with st.expander(f"{variable_name} — {len(df)} rows × {len(df.columns)} columns", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", report["rows"])
        c2.metric("Columns", report["columns"])
        c3.metric("Missing", report["missing_values"])
        c4.metric("Duplicates", report["duplicate_rows"])

        st.dataframe(df.head(100), use_container_width=True)

        if report["warnings"]:
            for warning in report["warnings"]:
                st.warning(warning)
        else:
            st.success("No major warnings detected.")

# -------------------- QUESTION --------------------
st.header("2. Ask a Question")
question = st.text_area(
    "Natural-language question",
    placeholder="Example: What is the total laptop sales?",
    height=90,
)

analyze = st.button("🔍 Analyze and Verify", type="primary", use_container_width=True)

if analyze:
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    if not api_ready:
        st.error("OPENAI_API_KEY is missing. Create a .env file from .env.example first.")
        st.stop()

    context = build_context(dataframes, quality_reports)

    # -------------------- ANSWERABILITY --------------------
    st.header("3. Answerability Check")

    with st.spinner("Checking whether the question can be answered reliably..."):
        try:
            decision = analyze_question(question, context)
        except Exception as exc:
            st.error(f"Question analysis failed: {exc}")
            st.stop()

    st.json(decision)

    status = str(decision.get("status", "")).upper()

    if status != "ANSWERABLE":
        if status == "NEEDS_CLARIFICATION":
            st.warning("⚠ The question needs clarification.")
        else:
            st.error("❌ The question cannot be answered reliably from the supplied data.")
        st.write("**Reason:**", decision.get("reason", "No reliable reason returned."))
        st.stop()

    # -------------------- CODE GENERATION --------------------
    st.header("4. Generated Proof Code")

    with st.spinner("Generating executable pandas code..."):
        try:
            code = generate_code(question, context)
        except Exception as exc:
            st.error(f"Code generation failed: {exc}")
            st.stop()

    st.code(code, language="python")

    # -------------------- VERIFICATION + REPAIR --------------------
    st.header("5. Verification")

    max_attempts = 3
    verification = None

    for attempt in range(1, max_attempts + 1):
        verification = execute_code(code, dataframes)

        if verification["success"]:
            break

        st.warning(f"Attempt {attempt} failed: {verification['error']}")

        if attempt < max_attempts:
            with st.spinner("Repairing the generated code..."):
                try:
                    schemas = context["tables"]
                    code = repair_code(
                        question,
                        schemas,
                        code,
                        verification["error"],
                    )
                    st.subheader(f"Repaired code — attempt {attempt + 1}")
                    st.code(code, language="python")
                except Exception as exc:
                    st.error(f"Code repair failed: {exc}")
                    break

    if not verification or not verification["success"]:
        st.error("❌ Verification could not be completed.")
        st.write("Do not trust an unverified result.")
        st.stop()

    result = verification["result"]

    st.success("✅ VERIFIED — the reported result comes from successfully executed code.")
    st.subheader("Verified Answer")
    st.metric("Result", str(result))

    st.subheader("Execution Output")
    st.code(verification["output"] or str(result))

    st.subheader("Final Evidence")
    st.write("**Question:**", question)
    st.write("**Answerability:**", decision.get("reason", "Answerable"))
    st.write("**Result source:** Executed verification code")

    warnings = []
    for name, report in quality_reports.items():
        warnings.extend([f"{name}: {w}" for w in report["warnings"]])

    if warnings:
        st.subheader("Data Warnings")
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No major data-quality warnings were found.")

    st.subheader("Re-runnable Proof")
    st.code(code, language="python")
