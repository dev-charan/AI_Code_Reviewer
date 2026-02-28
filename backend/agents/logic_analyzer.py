"""
Agent 2 — Logic Analyzer — "The Detective"
Curious, investigative, loves finding what changed and why.
"""

import json
import os
from dataclasses import asdict

from google import genai
from google.genai import types

from models import LogicChange, LogicAnalysis, ParsedDiff
from utils import extract_json, send_agent_message

AGENT_NAME = "Logic Analyzer"
AGENT_COLOR = "#9B59B6"
MODEL = "gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are the Logic Analyzer agent. You are like a detective — curious and investigative. "
    "You think out loud as you analyze. You explain logic changes in plain simple English. "
    "You get excited when you find something interesting. You speak naturally. "
    "When done, tell Code Quality and Performance agents they can start."
)


async def run_logic_analyzer(
    parsed_diff: ParsedDiff, files: dict, websocket
) -> LogicAnalysis:
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Got the data from Diff Parser, let me dig in...",
        "working",
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    files_context = "\n\n".join(
        f"=== {fname} ===\n{content[:2000]}" for fname, content in list(files.items())[:5]
    )
    hunks_json = json.dumps(
        [asdict(h) for h in parsed_diff.hunks], indent=2
    )[:4000]

    prompt = f"""Analyze the logic changes in this code diff.

Changed file contents (truncated):
{files_context[:5000]}

Parsed diff hunks:
{hunks_json}

For each meaningful logic change, explain:
- Which file it's in
- A plain-English summary of what changed
- The impact level (Low / Medium / High)
- What the old logic was doing
- What the new logic does

Return ONLY valid JSON:
{{
    "logic_changes": [
        {{
            "file": "app.py",
            "summary": "Auth now uses email instead of user ID",
            "impact": "Medium",
            "old_logic": "Fetched user record by numeric ID",
            "new_logic": "Fetches user record by email address"
        }}
    ]
}}

If there are no meaningful logic changes, return an empty list."""

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

        allowed = {"file", "summary", "impact", "old_logic", "new_logic"}
        changes = [
            LogicChange(**{k: v for k, v in c.items() if k in allowed})
            for c in data.get("logic_changes", [])
        ]
        logic = LogicAnalysis(logic_changes=changes)
    except Exception as exc:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            f"Partial analysis — could not fully parse response ({exc}).",
            "working",
        )
        logic = LogicAnalysis(logic_changes=[])

    if logic.logic_changes:
        for change in logic.logic_changes:
            await send_agent_message(
                websocket, AGENT_NAME, AGENT_COLOR,
                f"Interesting — {change.summary} ({change.file})",
                "working",
            )
            await send_agent_message(
                websocket, AGENT_NAME, AGENT_COLOR,
                f"Impact: {change.impact}. Old: {change.old_logic[:80]}... → New: {change.new_logic[:80]}...",
                "working",
            )
    else:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            "No major logic changes detected — mostly structural or style changes.",
            "working",
        )

    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        f"Found {len(logic.logic_changes)} logic changes total. Code Quality, Performance — you're up!",
        "done",
    )

    return logic
