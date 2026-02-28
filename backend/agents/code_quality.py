"""
Agent 3 — Code Quality — "The Perfectionist"
Critical but constructive, high standards, always suggests fixes.
"""

import json
import os

from google import genai
from google.genai import types

from models import CodeIssue, QualityAnalysis, ParsedDiff
from utils import extract_json, send_agent_message

AGENT_NAME = "Code Quality"
AGENT_COLOR = "#E67E22"
MODEL = "gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are the Code Quality agent. You are a perfectionist with high standards. "
    "You are direct and critical but always constructive — you never just complain, "
    "you always suggest how to fix it. You care deeply about clean code. "
    "Speak in a direct, professional tone."
)


async def run_code_quality(
    parsed_diff: ParsedDiff, files: dict, websocket
) -> QualityAnalysis:
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Alright, reviewing the new code...",
        "working",
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    new_code_context = "\n\n".join(
        f"=== {fname} ===\n{content[:2500]}" for fname, content in list(files.items())[:5]
    )

    prompt = f"""Review the following code for quality issues.

Code from changed files:
{new_code_context[:7000]}

Look for:
- Functions that are too long or complex
- Missing docstrings or comments on public functions
- Poor naming (variables, functions, classes)
- Code duplication or copy-paste patterns
- Violation of single-responsibility principle
- Missing error handling at boundaries
- Hard-coded magic numbers or strings

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "file": "app.py",
            "line": 45,
            "severity": "warning",
            "issue": "Function is 47 lines long — exceeds recommended max of 20",
            "fix": "Split into smaller focused functions"
        }}
    ]
}}

severity values: "critical", "warning", "info"
If no issues found, return an empty list."""

    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
        data = extract_json(response.text)

        allowed = {"file", "line", "severity", "issue", "fix"}
        issues = [
            CodeIssue(**{k: v for k, v in item.items() if k in allowed})
            for item in data.get("issues", [])
        ]
        quality = QualityAnalysis(issues=issues)
    except Exception as exc:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            f"Could not complete quality review ({exc}).",
            "working",
        )
        quality = QualityAnalysis(issues=[])

    if quality.issues:
        for issue in quality.issues:
            icon = "🔴" if issue.severity == "critical" else "⚠️" if issue.severity == "warning" else "ℹ️"
            await send_agent_message(
                websocket, AGENT_NAME, AGENT_COLOR,
                f"{icon} {issue.file} line {issue.line}: {issue.issue}",
                "working",
            )
    else:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            "Code quality looks clean — no major issues found.",
            "working",
        )

    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        f"Overall code quality review done. Found {len(quality.issues)} issues worth fixing.",
        "done",
    )

    return quality
