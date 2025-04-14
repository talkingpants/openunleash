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
                    "content": base64.b64encode("placeholder".encode()).decode()
                }
            )


def get_sha(path):
    r = requests.get(f"{API_URL}/repos/{REPO}/contents/{path}", headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def create_or_update_file(path, content, message, overwrite=False):
    ensure_dir(path)
    content_encoded = base64.b64encode(content.encode()).decode()
    sha = get_sha(path)

    if sha and not overwrite:
        raise Exception(f"File already exists: {path} (use action: update)")

    payload = {
        "message": message or f"update: {path}",
        "content": content_encoded
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(f"{API_URL}/repos/{REPO}/contents/{path}", headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"✅ File '{path}' created or updated.")


def delete_file(path, message):
    sha = get_sha(path)
    if not sha:
        raise Exception(f"File not found: {path}")

    payload = {
        "message": message or f"delete: {path}",
        "sha": sha
    }

    r = requests.delete(f"{API_URL}/repos/{REPO}/contents/{path}", headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"🗑️ File '{path}' deleted.")


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
        path = command.get("path")
        message = command.get("message", "via GPT bridge")

        if action == "create":
            create_or_update_file(path, command["content"], message, overwrite=False)
            comment_and_close(issue_number, f"✅ File `{path}` created.")

        elif action == "update":
            create_or_update_file(path, command["content"], message, overwrite=True)
            comment_and_close(issue_number, f"✅ File `{path}` updated.")

        elif action == "delete":
            delete_file(path, message)
            comment_and_close(issue_number, f"🗑️ File `{path}` deleted.")

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
