import re
from typing import Dict
import pandas as pd


def _schema(df: pd.DataFrame) -> dict:
    return {
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "rows": int(len(df)),
    }


def check_data_quality(df: pd.DataFrame) -> dict:
    warnings = []

    missing_by_column = {
        str(c): int(v) for c, v in df.isna().sum().items() if int(v) > 0
    }
    duplicate_rows = int(df.duplicated().sum())

    if missing_by_column:
        warnings.append(f"Missing values found: {missing_by_column}")
    if duplicate_rows:
        warnings.append(f"Duplicate rows found: {duplicate_rows}")

    currencies = []
    currency_cols = [c for c in df.columns if str(c).lower() in {"currency", "curr", "currency_code"}]
    for c in currency_cols:
        vals = df[c].dropna().astype(str).str.strip().unique().tolist()
        currencies.extend(vals)
    currencies = sorted(set(currencies))
    if len(currencies) > 1:
        warnings.append(f"Multiple currencies detected: {currencies}")

    date_columns = [c for c in df.columns if "date" in str(c).lower() or "time" in str(c).lower()]
    date_report = {}
    for c in date_columns:
        parsed = pd.to_datetime(df[c], errors="coerce", dayfirst=False)
        invalid = int(parsed.isna().sum())
        if invalid:
            date_report[str(c)] = invalid
            warnings.append(f"Some values in date/time column '{c}' could not be parsed reliably: {invalid}")

    # Heuristic for mixed numeric/text columns.
    mixed_columns = []
    for c in df.columns:
        non_null = df[c].dropna()
        if len(non_null) and non_null.map(lambda x: type(x).__name__).nunique() > 1:
            mixed_columns.append(str(c))
    if mixed_columns:
        warnings.append(f"Potential mixed data types in: {mixed_columns}")

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_values": int(df.isna().sum().sum()),
        "missing_by_column": missing_by_column,
        "duplicate_rows": duplicate_rows,
        "currencies": currencies,
        "date_report": date_report,
        "warnings": warnings,
        "schema": _schema(df),
    }


def build_context(dataframes: Dict[str, pd.DataFrame], quality_reports: Dict[str, dict]) -> dict:
    context = {"tables": {}, "quality": quality_reports}
    for name, df in dataframes.items():
        context["tables"][name] = {
            "variable_name": f"{_safe_name(name)}_df",
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "rows": int(len(df)),
            "sample": df.head(5).to_dict(orient="records"),
        }
    return context


def _safe_name(name: str) -> str:
    stem = str(name).rsplit("/", 1)[-1].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    stem = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_") or "table"
    if stem[0].isdigit():
        stem = "table_" + stem
    return stem.lower()
