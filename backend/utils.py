import json
from fastapi import WebSocket


async def send_agent_message(
    websocket: WebSocket,
    agent: str,
    color: str,
    message: str,
    status: str,
):
    msg_type = "agent_done" if status == "done" else "agent_message"
    await websocket.send_json({
        "type": msg_type,
        "agent": agent,
        "color": color,
        "message": message,
        "status": status,
    })


def extract_json(text: str) -> dict:
    """Robustly pull JSON out of a Gemini response that may wrap it in markdown."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)
