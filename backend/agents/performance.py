"""
Agent 4 — Performance — "The Optimizer"
Efficiency-obsessed, thinks in Big O, memory, and database queries.
"""

import os

from google import genai
from google.genai import types

from models import PerfIssue, PerfAnalysis, ParsedDiff
from utils import extract_json, send_agent_message

AGENT_NAME = "Performance"
AGENT_COLOR = "#F1C40F"
MODEL = "gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are the Performance agent. You are obsessed with efficiency and speed. "
    "You think in terms of Big O, memory usage, and database queries. "
    "You get genuinely excited when you see good optimizations. "
    "You point out inefficiencies clearly and explain why they matter. "
    "Speak with confidence and technical precision."
)


async def run_performance(
    parsed_diff: ParsedDiff, files: dict, websocket
) -> PerfAnalysis:
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Scanning for performance issues...",
        "working",
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    new_code_context = "\n\n".join(
        f"=== {fname} ===\n{content[:2500]}" for fname, content in list(files.items())[:5]
    )

    prompt = f"""Analyze the following code for performance problems and optimizations.

Code from changed files:
{new_code_context[:7000]}

Look for:
- N+1 query problems (loops that trigger database calls)
- Missing database indexes implied by query patterns
- Inefficient algorithms (nested loops on large data, O(n²) patterns)
- Repeated expensive computations that could be cached
- Memory leaks or unbounded growth
- Blocking I/O in async contexts
- Unnecessary list comprehensions over generators for large data
- Good optimizations that deserve a mention (positive findings too)

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "file": "app.py",
            "line": 34,
            "severity": "warning",
            "issue": "Potential N+1 query — Profile fetched inside loop over users",
            "fix": "Use select_related('profile') or prefetch_related to batch the query"
        }}
    ]
}}

severity values: "critical", "warning", "info", "good" (use "good" for positive findings)
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
            PerfIssue(**{k: v for k, v in item.items() if k in allowed})
            for item in data.get("issues", [])
        ]
        perf = PerfAnalysis(issues=issues)
    except Exception as exc:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            f"Could not complete performance scan ({exc}).",
            "working",
        )
        perf = PerfAnalysis(issues=[])

    if perf.issues:
        for issue in perf.issues:
            if issue.severity == "good":
                await send_agent_message(
                    websocket, AGENT_NAME, AGENT_COLOR,
                    f"✅ Nice — {issue.issue} ({issue.file} line {issue.line})",
                    "working",
                )
            else:
                icon = "🔴" if issue.severity == "critical" else "⚠️"
                await send_agent_message(
                    websocket, AGENT_NAME, AGENT_COLOR,
                    f"{icon} {issue.file} line {issue.line}: {issue.issue}",
                    "working",
                )
    else:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            "No performance issues detected. Code looks efficient.",
            "working",
        )

    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        f"Performance scan complete. Found {len(perf.issues)} items.",
        "done",
    )

    return perf
