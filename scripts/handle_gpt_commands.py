import os
import json
import base64
import requests
from pathlib import Path

REPO = os.getenv("GITHUB_REPOSITORY")
TOKEN = os.getenv("GH_TOKEN")
API_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_latest_labeled_issue():
    r = requests.get(f"{API_URL}/repos/{REPO}/issues?labels=gpt-command&state=open&per_page=1", headers=HEADERS)
    r.raise_for_status()
    issues = r.json()
    return issues[0] if issues else None

def ensure_dir(path):
    """Ensure all intermediate folders are committed (GitHub API does not auto-create dirs)."""
    parts = Path(path).parent.parts
    for i in range(1, len(parts) + 1):
        subpath = "/".join(parts[:i]) + "/.keep"
        r = requests.get(f"{API_URL}/repos/{REPO}/contents/{subpath}", headers=HEADERS)
        if r.status_code == 404:
            print(f"📁 Creating missing dir placeholder: {subpath}")
            requests.put(
                f"{API_URL}/repos/{REPO}/contents/{subpath}",
                headers=HEADERS,
                json={
                    "message": f"chore: create folder placeholder for {subpath}",
                    "content": base64.b64encode(b"placeholder").decode()
                }
            )

def create_or_update_file(path, content, message):
    ensure_dir(path)

    content_encoded = base64.b64encode(content.encode()).decode()
    url = f"{API_URL}/repos/{REPO}/contents/{path}"

    # If updating, fetch SHA
    sha = None
    r = requests.get(url, headers=HEADERS)
    if r.ok:
        sha = r.json().get("sha")

    payload = {
        "message": message or f"Update {path}",
        "content": content_encoded
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"✅ File '{path}' created or updated.")

def comment_and_close(issue_number, message):
    requests.post(
        f"{API_URL}/repos/{REPO}/issues/{issue_number}/comments",
        headers=HEADERS,
        json={"body": message}
    )
    requests.patch(
        f"{API_URL}/repos/{REPO}/issues/{issue_number}",
        headers=HEADERS,
        json={"state": "closed"}
    )

def parse_and_execute(issue):
    issue_number = issue["number"]
    try:
        body = issue["body"]
        print(f"📥 Issue Body:\n{body}")
        command = json.loads(body)
        action = command.get("action")
        message = command.get("message", "update via GPT")

        if action in ("create", "update"):
            path = command["path"]
            content = command.get("content", "")
            create_or_update_file(path, content, message)
            comment_and_close(issue_number, f"✅ `{action}` succeeded for `{path}`.")
        elif action == "comment":
            comment_and_close(command["issue_number"], command.get("content", "✅ Done."))
        else:
            raise ValueError(f"Unsupported action: {action}")
    except Exception as e:
        error = f"❌ GPT Command failed: {str(e)}"
        print(error)
        comment_and_close(issue_number, error)

if __name__ == "__main__":
    issue = get_latest_labeled_issue()
    if issue:
        parse_and_execute(issue)
    else:
        print("ℹ️ No open gpt-command issues found.")
