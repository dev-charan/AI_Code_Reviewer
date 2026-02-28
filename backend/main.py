"""
main.py — FastAPI app with a single WebSocket endpoint.

Run with:
    cd backend
    uvicorn main:app --reload
"""

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=False))  # walks up from backend/ to find .env anywhere

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from pipeline import run_pipeline

app = FastAPI(title="Git Diff Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Git Diff Analyzer API is running. Connect via WebSocket at /ws"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        repo_url: str = data.get("repo_url", "").strip()

        if not repo_url:
            await websocket.send_json({"type": "error", "message": "repo_url is required."})
            return

        if "github.com" not in repo_url:
            await websocket.send_json({"type": "error", "message": "Only GitHub URLs are supported."})
            return

        await run_pipeline(repo_url, websocket)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
