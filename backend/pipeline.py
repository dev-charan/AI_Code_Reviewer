"""
pipeline.py — The conductor.
Runs all 5 agents in order and passes data between them.
"""

from fastapi import WebSocket

from tools.github_tool import get_latest_diff
from agents.diff_parser import run_diff_parser
from agents.logic_analyzer import run_logic_analyzer
from agents.code_quality import run_code_quality
from agents.performance import run_performance
from agents.report_writer import run_report_writer
from utils import send_agent_message


async def run_pipeline(repo_url: str, websocket: WebSocket):
    try:
        # ── Step 0: Fetch from GitHub ─────────────────────────────────────
        await websocket.send_json({
            "type": "status",
            "message": f"Fetching latest commit from {repo_url}...",
        })
        github_data = get_latest_diff(repo_url)
        await websocket.send_json({
            "type": "status",
            "message": f"Got commit {github_data.commit_sha} — {len(github_data.files)} file(s) changed.",
        })

        # ── Step 1: Diff Parser ──────────────────────────────────────────
        parsed_diff = await run_diff_parser(github_data, websocket)

        # ── Step 2: Logic Analyzer ───────────────────────────────────────
        logic = await run_logic_analyzer(parsed_diff, github_data.files, websocket)

        # ── Step 3a: Code Quality ────────────────────────────────────────
        quality = await run_code_quality(parsed_diff, github_data.files, websocket)

        # ── Step 3b: Performance ─────────────────────────────────────────
        perf = await run_performance(parsed_diff, github_data.files, websocket)

        # ── Step 4: Report Writer ────────────────────────────────────────
        report = await run_report_writer(
            github_data, parsed_diff, logic, quality, perf, websocket
        )

        # ── Send final report to frontend ────────────────────────────────
        await websocket.send_json({
            "type": "report_ready",
            "report": report,
        })

    except Exception as exc:
        await websocket.send_json({
            "type": "error",
            "message": f"Pipeline failed: {exc}",
        })
