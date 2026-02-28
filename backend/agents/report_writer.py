"""
Agent 5 — Report Writer — "The Journalist"
Polished, clear communicator. Turns messy findings into readable markdown.
"""

import json
import os
from dataclasses import asdict
from datetime import date

from google import genai
from google.genai import types

from models import LogicAnalysis, ParsedDiff, PerfAnalysis, QualityAnalysis
from utils import send_agent_message

AGENT_NAME = "Report Writer"
AGENT_COLOR = "#2ECC71"
MODEL = "gemini-3-flash-preview"

SYSTEM_PROMPT = (
    "You are the Report Writer agent. You are a skilled technical writer. "
    "You take findings from all other agents and turn them into a clear, "
    "well-structured markdown report. You are polished and professional. "
    "You prioritize clarity — the report should be useful to a solo developer."
)


async def run_report_writer(
    github_data,
    parsed_diff: ParsedDiff,
    logic: LogicAnalysis,
    quality: QualityAnalysis,
    perf: PerfAnalysis,
    websocket,
) -> str:
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Got all the findings from the team.",
        "working",
    )
    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Organizing by severity — critical issues first.",
        "working",
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    findings = {
        "repository": github_data.repo,
        "commit": github_data.commit_sha,
        "date": date.today().isoformat(),
        "parsed_diff": asdict(parsed_diff),
        "logic_analysis": asdict(logic),
        "quality_analysis": asdict(quality),
        "performance_analysis": asdict(perf),
    }

    prompt = f"""Generate a comprehensive git diff analysis report in clean markdown.

Findings from all agents:
{json.dumps(findings, indent=2)[:10000]}

Write a professional markdown report with these sections:

# Git Diff Analysis Report

Meta block (repo, commit, date)

## 📁 Files Changed
List each file with additions/deletions count.

## 🧠 Logic Changes
For each logic change: what changed, impact level, old vs new with code blocks if available.

## 🏗️ Code Quality Issues
Table: Severity | File | Line | Issue | Fix

## ⚡ Performance Issues
Table: Severity | File | Line | Issue | Fix

## 🔧 Suggested Code Fixes
For any critical/warning issues that have a clear fix, show a Before/After code block.

## 📊 Summary Score
Table with Logic, Code Quality, Performance, Overall scores out of 10.
Base scores on the number and severity of issues found.

Be specific and actionable. Use emoji section headers as shown."""

    try:
        await send_agent_message(
            websocket, AGENT_NAME, AGENT_COLOR,
            "Writing the report now...",
            "working",
        )
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        report = response.text
    except Exception as exc:
        report = _fallback_report(github_data, parsed_diff, logic, quality, perf, str(exc))

    await send_agent_message(
        websocket, AGENT_NAME, AGENT_COLOR,
        "Done. Here is your full analysis report.",
        "done",
    )

    return report


def _fallback_report(github_data, parsed_diff, logic, quality, perf, error: str) -> str:
    """Minimal markdown report if Gemini call fails."""
    lines = [
        "# Git Diff Analysis Report",
        f"**Repository:** {github_data.repo}",
        f"**Commit:** {github_data.commit_sha}",
        f"**Date:** {date.today().isoformat()}",
        "",
        f"> ⚠️ Report generation encountered an issue: {error}",
        "",
        "## 📁 Files Changed",
    ]
    for f in parsed_diff.files_changed:
        lines.append(f"- `{f}`")

    lines += ["", "## 🧠 Logic Changes"]
    for c in logic.logic_changes:
        lines.append(f"- **{c.file}**: {c.summary} (Impact: {c.impact})")

    lines += ["", "## 🏗️ Code Quality Issues"]
    for i in quality.issues:
        lines.append(f"- `{i.file}` line {i.line} [{i.severity}]: {i.issue} → {i.fix}")

    lines += ["", "## ⚡ Performance Issues"]
    for i in perf.issues:
        lines.append(f"- `{i.file}` line {i.line} [{i.severity}]: {i.issue} → {i.fix}")

    return "\n".join(lines)
