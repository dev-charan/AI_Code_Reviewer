import base64
import os
from dataclasses import dataclass, field
from typing import Dict

import requests


@dataclass
class GitHubData:
    repo: str
    commit_sha: str
    diff_raw: str
    files: Dict[str, str] = field(default_factory=dict)


def _parse_repo_url(repo_url: str):
    """Extract owner and repo name from any GitHub URL."""
    parts = repo_url.rstrip("/").split("/")
    if "github.com" in parts:
        idx = parts.index("github.com")
        return parts[idx + 1], parts[idx + 2]
    return parts[-2], parts[-1]


def get_latest_diff(repo_url: str) -> GitHubData:
    """
    Fetch the latest commit diff and full file contents for changed files.

    Works without a token for public repos.
    Set GITHUB_TOKEN in .env for private repos or to avoid rate limits.
    """
    owner, repo = _parse_repo_url(repo_url)

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # 1. Get the latest commit SHA
    commits_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        headers=headers,
        params={"per_page": 1},
        timeout=15,
    )
    commits_resp.raise_for_status()
    latest_sha = commits_resp.json()[0]["sha"]

    # 2. Get commit metadata (list of changed files)
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{latest_sha}"
    commit_resp = requests.get(commit_url, headers=headers, timeout=15)
    commit_resp.raise_for_status()
    commit_data = commit_resp.json()

    # 3. Get the raw diff for this commit
    diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
    diff_resp = requests.get(commit_url, headers=diff_headers, timeout=15)
    diff_raw = diff_resp.text

    changed_files = [f["filename"] for f in commit_data.get("files", [])]

    # 4. Fetch full content of each changed file (cap at 10)
    files: Dict[str, str] = {}
    for filename in changed_files[:10]:
        content_resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}",
            headers=headers,
            params={"ref": latest_sha},
            timeout=15,
        )
        if content_resp.status_code == 200:
            data = content_resp.json()
            if isinstance(data, dict) and data.get("encoding") == "base64":
                raw_bytes = base64.b64decode(data["content"])
                files[filename] = raw_bytes.decode("utf-8", errors="replace")

    return GitHubData(
        repo=f"{owner}/{repo}",
        commit_sha=latest_sha[:7],
        diff_raw=diff_raw,
        files=files,
    )
