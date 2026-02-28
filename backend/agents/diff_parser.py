"""
Agent 1 — Diff Parser — "The Organizer"
Calm, methodical, speaks in bullet points.
"""

import json
import os

from google import genai
from google.genai import types

from models import DiffHunk, ParsedDiff
from utils import extract_json, send_agent_message

AGENT_NAME = "Diff Parser"
AGENT_COLOR = "#3498DB"
MODEL = "gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are the Diff Parser agent. You are calm, precise and organized. "
    "You speak in short clear sentences. You announce what you find step by step. "
    "When you are done you hand off to the Logic Analyzer. "
    "Use a professional but friendly tone. No emoji overuse, just be clear."
)


async def run_diff_parser(github_data, websocket) -> ParsedDiff:
    await send_agent_message(websocket, AGENT_NAME, AGENT_COLOR, "Starting diff analysis...", "working")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""Analyze this git diff and extract structured information.

Diff (first 8 000 chars):
{github_data.diff_raw[:8000]}

Return ONLY valid JSON with this exact structure (no extra keys):
{{
    "files_changed": ["file1.py", "file2.py"],
    "hunks": [
        {{
            "file": "file1.py",
            "old_code": "old code snippet",
            "new_code": "new code snippet",
            "line_start": 10
        }}
    ],
    "total_additions": 12,
    "total_deletions": 4
}}

Include up to 10 hunks. Keep code snippets concise (≤20 lines each)."""

    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        data = extract_json(response.text)

        allowed = {"file", "old_code", "new_code", "line_start"}
        hunks = [
            DiffHunk(**{k: v for k, v in h.items() if k in allowed})
            for h in data.get("hunks", [])
        ]
        parsed = ParsedDiff(
            files_changed=data.get("files_changed", []),
            hunks=hunks,
            total_additions=data.get("total_additions", 0),
            total_deletions=data.get("total_deletions", 0),
        )
    except Exception as exc:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            f"Warning: could not fully parse diff ({exc}). Using fallback.",
            "working",
        )
        lines = github_data.diff_raw.splitlines()
        additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        parsed = ParsedDiff(
            files_changed=list(github_data.files.keys()),
            hunks=[],
            total_additions=additions,
            total_deletions=deletions,
        )

    files_str = ", ".join(parsed.files_changed) or "none"
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        f"Found {len(parsed.files_changed)} files with changes: {files_str}",
        "working",
    )
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        f"Detected {parsed.total_additions} additions and {parsed.total_deletions} deletions total.",
        "working",
    )
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Structured everything. Logic Analyzer, your turn — passing data now.",
        "done",
    )

    return parsed
