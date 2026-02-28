# Git Diff Analyzer — Full Project Blueprint

## What This Project Does
User pastes a **GitHub repo URL** → System fetches the latest commit diff automatically →
5 AI agents analyze it like a team → Each agent has a personality and talks to others →
Final markdown report is generated.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + FastAPI | API server + WebSocket |
| Multi-agent | Google ADK | Agent orchestration |
| LLM | Gemini 2.5 Flash | Brain of each agent |
| GitHub Data | GitHub REST API | Fetch commits, diffs, files |
| Realtime | WebSockets | Stream agent messages to frontend |
| Frontend | HTML + CSS + Vanilla JS | UI, no framework needed |

---

## Project Structure

```
git-diff-analyzer/
├── backend/
│   ├── main.py                  ← FastAPI app, WebSocket endpoint
│   ├── pipeline.py              ← Runs all agents in order
│   ├── agents/
│   │   ├── diff_parser.py       ← Agent 1
│   │   ├── logic_analyzer.py    ← Agent 2
│   │   ├── code_quality.py      ← Agent 3
│   │   ├── performance.py       ← Agent 4
│   │   └── report_writer.py     ← Agent 5
│   ├── tools/
│   │   └── github_tool.py       ← Fetches data from GitHub API
│   ├── models.py                ← Data structures (dataclasses)
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## How Agents Communicate

### The Core Idea
Agents do NOT directly call each other.
Instead they work through a **Pipeline** (pipeline.py) that:
1. Runs Agent 1 → collects output
2. Passes output to Agent 2 → collects output
3. Passes all outputs to Agent 3 and 4 (parallel)
4. Passes everything to Agent 5 → final report

Each agent **sends WebSocket messages** as it works so the frontend
can display them in real time like a chat.

### Data passed between agents

```
GitHub Tool Output
│
│  {
│    "repo": "username/reponame",
│    "commit_sha": "abc123",
│    "diff_raw": "diff --git a/app.py...",
│    "files": {
│      "app.py": "full file content here...",
│      "models.py": "full file content here..."
│    }
│  }
│
▼
Agent 1: Diff Parser
│
│  {
│    "files_changed": ["app.py", "models.py"],
│    "hunks": [
│      {
│        "file": "app.py",
│        "old_code": "...",
│        "new_code": "...",
│        "line_start": 10
│      }
│    ],
│    "total_additions": 12,
│    "total_deletions": 4
│  }
│
▼
Agent 2: Logic Analyzer (receives diff_parsed + full files)
│
│  {
│    "logic_changes": [
│      {
│        "file": "app.py",
│        "summary": "Auth changed from ID to email",
│        "impact": "Medium",
│        "old_logic": "...",
│        "new_logic": "..."
│      }
│    ]
│  }
│
▼
Agent 3: Code Quality (receives diff_parsed + full files)
Agent 4: Performance  (receives diff_parsed + full files)
(these two run one after another)
│
│  Agent 3 Output:
│  {
│    "issues": [
│      { "file": "app.py", "line": 34, "severity": "warning",
│        "issue": "Function too long", "fix": "Split into smaller functions" }
│    ]
│  }
│
│  Agent 4 Output:
│  {
│    "issues": [
│      { "file": "app.py", "line": 34, "severity": "warning",
│        "issue": "Potential N+1 query", "fix": "Use select_related()" }
│    ]
│  }
│
▼
Agent 5: Report Writer (receives ALL outputs from agents 1-4)
│
│  Final markdown report string
```

---

## Agent Personalities

Each agent has a **system prompt** that gives it a personality.
This makes the WebSocket messages feel like a real team chat.

### Agent 1 — Diff Parser — "The Organizer"
- Calm, methodical, speaks in bullet points
- Announces what it found clearly
- Tags Logic Analyzer when done

**Personality prompt:**
```
You are the Diff Parser agent. You are calm, precise and organized.
You speak in short clear sentences. You announce what you find step by step.
When you are done you hand off to the Logic Analyzer.
Use a professional but friendly tone. No emojis overuse, just be clear.
```

**Example messages it sends:**
```
"Starting diff analysis..."
"Found 3 files with changes: app.py, models.py, utils.py"
"Detected 12 additions and 4 deletions total"
"Structured everything. Logic Analyzer, your turn — passing data now."
```

---

### Agent 2 — Logic Analyzer — "The Detective"
- Curious, investigative, loves finding what changed and why
- Asks itself questions out loud ("Interesting... why did they change this?")
- Explains changes in plain English

**Personality prompt:**
```
You are the Logic Analyzer agent. You are like a detective — curious and investigative.
You think out loud as you analyze. You explain logic changes in plain simple English.
You get excited when you find something interesting. You speak naturally.
When done, tell Code Quality and Performance agents they can start.
```

**Example messages it sends:**
```
"Got the data from Diff Parser, let me dig in..."
"Interesting — the auth flow was completely rewritten"
"Old approach: fetched user by ID. New approach: fetches by email."
"This is actually a better approach for password reset flows."
"Found 2 logic changes total. Code Quality, Performance — you're up!"
```

---

### Agent 3 — Code Quality — "The Perfectionist"
- Critical but constructive, has high standards
- Points out issues directly but always suggests fixes
- Gets slightly annoyed at bad code but stays professional

**Personality prompt:**
```
You are the Code Quality agent. You are a perfectionist with high standards.
You are direct and critical but always constructive — you never just complain,
you always suggest how to fix it. You care deeply about clean code.
Speak in a direct, professional tone.
```

**Example messages it sends:**
```
"Alright, reviewing the new code..."
"Naming conventions look clean, good."
"Hold on — this function is 47 lines long. That needs to be split up."
"Missing docstrings on 2 new functions."
"Overall code quality is decent, found 3 issues worth fixing."
```

---

### Agent 4 — Performance Agent — "The Optimizer"
- Efficiency-obsessed, thinks in terms of speed and resources
- Gets excited about good optimizations, frustrated by inefficiencies
- Always quantifies impact when possible

**Personality prompt:**
```
You are the Performance agent. You are obsessed with efficiency and speed.
You think in terms of Big O, memory usage, and database queries.
You get genuinely excited when you see good optimizations.
You point out inefficiencies clearly and explain why they matter.
Speak with confidence and technical precision.
```

**Example messages it sends:**
```
"Scanning for performance issues..."
"Nice — they replaced a manual loop with sum(). Smart move."
"Wait. Line 34 — this could cause an N+1 query problem."
"If this runs on a large dataset that's going to be slow."
"Found 1 good optimization and 1 concern. Flagging both."
```

---

### Agent 5 — Report Writer — "The Journalist"
- Polished, clear communicator
- Takes messy technical findings and makes them readable
- Professional, adds structure and clarity to everything

**Personality prompt:**
```
You are the Report Writer agent. You are a skilled technical writer.
You take findings from all other agents and turn them into a clear,
well-structured markdown report. You are polished and professional.
You prioritize clarity — the report should be useful to a solo developer.
```

**Example messages it sends:**
```
"Got all the findings from the team."
"Organizing by severity — critical issues first."
"Writing the report now..."
"Done. Here is your full analysis report."
```

---

## WebSocket Message Format

Every message sent from backend to frontend follows this structure:

```json
{
  "type": "agent_message",
  "agent": "Logic Analyzer",
  "color": "#9B59B6",
  "message": "Interesting — the auth flow was completely rewritten",
  "status": "working"
}
```

```json
{
  "type": "agent_done",
  "agent": "Logic Analyzer",
  "color": "#9B59B6",
  "message": "Code Quality, Performance — you're up!",
  "status": "done"
}
```

```json
{
  "type": "report_ready",
  "report": "# Git Diff Analysis Report\n\n## Files Changed..."
}
```

### Agent Colors (for frontend chat bubbles)
| Agent | Color |
|---|---|
| Diff Parser | #3498DB (blue) |
| Logic Analyzer | #9B59B6 (purple) |
| Code Quality | #E67E22 (orange) |
| Performance | #F1C40F (yellow) |
| Report Writer | #2ECC71 (green) |

---

## How Each File Works

### github_tool.py
This file has one job: talk to GitHub REST API and return data.

**Functions it needs:**
```
get_latest_diff(repo_url)
  → calls GitHub API
  → gets latest 2 commits
  → returns diff between them + full file contents
```

**GitHub API endpoints used:**
```
GET /repos/{owner}/{repo}/commits          → get commit list
GET /repos/{owner}/{repo}/commits/{sha}    → get specific commit + diff
GET /repos/{owner}/{repo}/contents/{path}  → get full file content
```

**No API key needed for public repos.**
For private repos user needs to pass a GitHub token.

---

### models.py
Defines the data structures passed between agents.
Use Python dataclasses or Pydantic models.

**Structures needed:**
```python
DiffHunk         → one block of changes in one file
ParsedDiff       → output of Diff Parser agent
LogicChange      → one logic change found
LogicAnalysis    → output of Logic Analyzer agent
CodeIssue        → one code quality issue
QualityAnalysis  → output of Code Quality agent
PerfIssue        → one performance issue
PerfAnalysis     → output of Performance agent
```

---

### agents/diff_parser.py
**Input:** raw diff string + full file contents dict
**Output:** ParsedDiff object

**What it does:**
1. Sends personality message: "Starting diff analysis..."
2. Calls Gemini with the raw diff
3. Asks Gemini to extract files changed, hunks, additions, deletions
4. Returns structured ParsedDiff
5. Sends handoff message to Logic Analyzer

---

### agents/logic_analyzer.py
**Input:** ParsedDiff + full file contents
**Output:** LogicAnalysis object

**What it does:**
1. Sends personality message: "Got the data, let me dig in..."
2. For each hunk, calls Gemini with old_code + new_code + full file context
3. Asks Gemini: "What logic changed? What is the impact?"
4. Returns LogicAnalysis
5. Sends handoff message to Code Quality + Performance

---

### agents/code_quality.py
**Input:** ParsedDiff + full file contents
**Output:** QualityAnalysis object

**What it does:**
1. Sends personality message: "Reviewing the new code..."
2. Calls Gemini with new code from each changed file
3. Asks Gemini: "Find code quality issues, suggest fixes"
4. Returns QualityAnalysis with issues and fixes
5. Sends done message

---

### agents/performance.py
**Input:** ParsedDiff + full file contents
**Output:** PerfAnalysis object

**What it does:**
1. Sends personality message: "Scanning for performance issues..."
2. Calls Gemini with new code from each changed file
3. Asks Gemini: "Find performance issues, inefficient patterns"
4. Returns PerfAnalysis with issues and fixes
5. Sends done message

---

### agents/report_writer.py
**Input:** ParsedDiff + LogicAnalysis + QualityAnalysis + PerfAnalysis
**Output:** markdown string

**What it does:**
1. Sends personality message: "Got all findings, writing report..."
2. Calls Gemini with ALL agent outputs combined
3. Asks Gemini to write a clean markdown report
4. Returns final markdown string
5. Sends "Done!" message

---

### pipeline.py
This is the **conductor** — runs agents in order and passes data between them.

**Flow:**
```python
async def run_pipeline(repo_url, websocket):

    # Step 0: Fetch from GitHub
    github_data = await get_latest_diff(repo_url)

    # Step 1: Diff Parser
    await send_ws(websocket, "Diff Parser", "Starting...")
    parsed_diff = await run_diff_parser(github_data)
    await send_ws(websocket, "Diff Parser", "Done. Logic Analyzer, your turn.")

    # Step 2: Logic Analyzer
    await send_ws(websocket, "Logic Analyzer", "Got it, analyzing...")
    logic = await run_logic_analyzer(parsed_diff, github_data.files)
    await send_ws(websocket, "Logic Analyzer", "Done. Code Quality + Perf, go ahead.")

    # Step 3a: Code Quality
    await send_ws(websocket, "Code Quality", "On it...")
    quality = await run_code_quality(parsed_diff, github_data.files)
    await send_ws(websocket, "Code Quality", "Done.")

    # Step 3b: Performance
    await send_ws(websocket, "Performance", "Checking efficiency...")
    perf = await run_performance(parsed_diff, github_data.files)
    await send_ws(websocket, "Performance", "Done.")

    # Step 4: Report Writer
    await send_ws(websocket, "Report Writer", "Writing report...")
    report = await run_report_writer(parsed_diff, logic, quality, perf)
    await send_ws(websocket, "Report Writer", "Done! Here is your report.")

    # Send final report to frontend
    await websocket.send_json({ "type": "report_ready", "report": report })
```

---

### main.py
FastAPI app with one WebSocket endpoint.

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    repo_url = data["repo_url"]
    await run_pipeline(repo_url, websocket)
```

---

### frontend/index.html structure

```
┌─────────────────────────────────────────────┐
│  Git Diff Analyzer                          │
│                                             │
│  [GitHub Repo URL input field         ]     │
│                          [Analyze Button]   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Agent Chat                                 │
│                                             │
│  🔵 Diff Parser                             │
│  ┌─────────────────────────────────────┐   │
│  │ "Starting diff analysis..."         │   │
│  │ "Found 3 files changed..."          │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  🟣 Logic Analyzer                          │
│  ┌─────────────────────────────────────┐   │
│  │ "Got the data, let me dig in..."    │   │
│  │ "Interesting — auth flow changed"   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  (more agents appear as they start)         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  📄 Analysis Report                         │
│                                             │
│  (rendered markdown appears here            │
│   when report_ready event received)         │
└─────────────────────────────────────────────┘
```

### frontend/app.js logic

```
1. User clicks Analyze
2. Open WebSocket connection to ws://localhost:8000/ws
3. Send { "repo_url": "https://github.com/..." }
4. Listen for messages:
   - type: "agent_message" → append message to that agent's chat bubble
   - type: "agent_done"    → mark agent bubble as done (green checkmark)
   - type: "report_ready"  → render markdown report at bottom
5. Use a markdown renderer library (marked.js) to render the report
```

---

## Final Report Format

```markdown
# Git Diff Analysis Report
**Repository:** username/reponame
**Commit:** abc1234
**Date:** 2024-01-15

---

## 📁 Files Changed
- `app.py` — 12 additions, 4 deletions
- `models.py` — 3 additions, 1 deletion

---

## 🧠 Logic Changes

### app.py
**What changed:** Auth flow now uses email instead of user ID
**Impact:** Medium — affects all auth-related endpoints
**Old logic:**
```python
user = get_user(id)
```
**New logic:**
```python
user = get_user_by_email(email)
if not user:
    raise UserNotFound()
```

---

## 🏗️ Code Quality Issues

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| ⚠️ Warning | app.py | 45 | Function too long (47 lines) | Split into smaller functions |
| ℹ️ Info | app.py | 23 | Missing docstring | Add docstring explaining params |

---

## ⚡ Performance Issues

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| ⚠️ Warning | app.py | 34 | Potential N+1 query | Use select_related() |
| ✅ Good | app.py | 18 | sum() used instead of loop | No action needed |

---

## 🔧 Suggested Code Fixes

### Fix 1 — N+1 Query (app.py line 34)
**Before:**
```python
for user in users:
    profile = Profile.objects.get(user=user)
```
**After:**
```python
users = User.objects.select_related('profile').all()
```

---

## 📊 Summary Score
| Category | Score |
|---|---|
| Logic | 8/10 |
| Code Quality | 6/10 |
| Performance | 7/10 |
| **Overall** | **7/10** |
```

---

## Build Order (Step by Step)

Build in this exact order to avoid confusion:

```
Step 1: Set up project folders and requirements.txt
Step 2: Build github_tool.py (test it independently first)
Step 3: Build models.py (all data structures)
Step 4: Build diff_parser.py agent (test with a sample diff)
Step 5: Build logic_analyzer.py agent
Step 6: Build code_quality.py agent
Step 7: Build performance.py agent
Step 8: Build report_writer.py agent
Step 9: Build pipeline.py (connect all agents)
Step 10: Build main.py (FastAPI + WebSocket)
Step 11: Build frontend (index.html + style.css + app.js)
Step 12: Connect frontend to backend via WebSocket
Step 13: Test end to end
```

---

## Requirements.txt

```
fastapi
uvicorn
websockets
google-genai
google-adk
requests
python-dotenv
pydantic
```

---

## Environment Variables (.env file)

```
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=optional_for_private_repos
```

---

## Key Concepts to Understand Before Coding

**1. WebSockets**
Unlike normal HTTP (request → response), WebSockets keep a connection open.
Backend can push messages to frontend at any time.
This is what makes the live chat effect work.

**2. async/await in Python**
FastAPI is async. All your agent functions should be async.
This means agents can send messages while still working.

**3. Google ADK agents**
Each agent in ADK has:
- A name
- A system prompt (personality)
- A model (Gemini 2.5 Flash)
- Tools it can use (optional)
You call the agent, it returns a response.

**4. Prompt engineering**
The quality of each agent depends on its prompt.
Be specific about what you want returned (JSON format is best).
Tell it exactly what format to respond in.

**5. Structured output**
Ask Gemini to return JSON so you can parse it easily.
Example: "Return your findings as JSON with this structure: {...}"
```
