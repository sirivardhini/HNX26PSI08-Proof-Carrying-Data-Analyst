import json
import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

from prompts import QUESTION_ANALYZER_PROMPT, CODE_GENERATOR_PROMPT, REPAIR_PROMPT

load_dotenv()


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=key)


def _clean_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def analyze_question(question: str, context: dict) -> dict:
    prompt = (
        QUESTION_ANALYZER_PROMPT
        + "\nUSER QUESTION:\n"
        + question
        + "\n\nDATA CONTEXT:\n"
        + json.dumps(context, indent=2, default=str)
    )
    response = _client().responses.create(model="gpt-5", input=prompt)
    return _clean_json(response.output_text)


def generate_code(question: str, context: dict) -> str:
    prompt = (
        CODE_GENERATOR_PROMPT
        + "\nUSER QUESTION:\n"
        + question
        + "\n\nAVAILABLE DATA:\n"
        + json.dumps(context, indent=2, default=str)
    )
    response = _client().responses.create(model="gpt-5", input=prompt)
    return _strip_fences(response.output_text)


def repair_code(question: str, schemas: dict, code: str, error: str) -> str:
    prompt = REPAIR_PROMPT.format(
        question=question,
        schemas=json.dumps(schemas, indent=2, default=str),
        code=code,
        error=error,
    )
    response = _client().responses.create(model="gpt-5", input=prompt)
    return _strip_fences(response.output_text)


def _strip_fences(text: str) -> str:
    code = text.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines).strip()
    return code
