import ast
import contextlib
import io
from typing import Dict

import pandas as pd

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool,
    "dict": dict, "enumerate": enumerate, "float": float,
    "int": int, "len": len, "list": list, "max": max,
    "min": min, "range": range, "round": round, "set": set,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
    "zip": zip,
}

FORBIDDEN_NAMES = {
    "__import__", "eval", "exec", "open", "compile", "input",
    "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "breakpoint", "help", "dir",
}

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "requests", "shutil",
    "pathlib", "builtins", "importlib",
}


def validate_code(code: str) -> None:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Imports are not allowed in verification code.")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"Forbidden operation/name: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("Dunder attribute access is not allowed.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "open", "compile", "__import__"}:
                raise ValueError(f"Forbidden function call: {node.func.id}")


def execute_code(code: str, dataframes: Dict[str, pd.DataFrame]):
    output = io.StringIO()

    try:
        validate_code(code)

        env = {"__builtins__": SAFE_BUILTINS, "pd": pd}
        env.update({name: df.copy() for name, df in dataframes.items()})
        local_vars = {}

        with contextlib.redirect_stdout(output):
            exec(code, env, local_vars)

        if "result" not in local_vars:
            raise ValueError("Generated code did not create a variable named `result`.")

        result = local_vars["result"]

        return {
            "success": True,
            "result": result,
            "output": output.getvalue(),
            "error": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "result": None,
            "output": output.getvalue(),
            "error": f"{type(exc).__name__}: {exc}",
        }
