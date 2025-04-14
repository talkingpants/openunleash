import os
import requests
import base64

REPO = os.getenv("GITHUB_REPOSITORY")
TOKEN = os.getenv("GH_TOKEN")
API_URL = "https://api.github.com"

def get_latest_labeled_issue():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(f"{API_URL}/repos/{REPO}/issues?labels=gpt-command&state=open&per_page=1", headers=headers)
    r.raise_for_status()
    issues = r.json()
    return issues[0] if issues else None

def parse_and_execute(issue):
    body = issue.get("body", "")
    issue_number = issue["number"]
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    try:
        import json
        command = json.loads(body)
        action = command.get("action")

        if action in ["create", "update"]:
            path = command["path"]
            content = base64.b64encode(command["content"].encode()).decode()
            message = command.get("message", f"{action}: {path}")

            # Fetch sha if updating
            sha = None
            if action == "update":
                r = requests.get(f"{API_URL}/repos/{REPO}/contents/{path}", headers=headers)
                if r.ok:
                    sha = r.json()["sha"]

            payload = {
                "message": message,
                "content": content
            }
            if sha:
                payload["sha"] = sha

            r = requests.put(f"{API_URL}/repos/{REPO}/contents/{path}", headers=headers, json=payload)
            r.raise_for_status()
            result = f"✅ `{action}` succeeded for `{path}`."

        elif action == "comment":
            comment = command.get("content", "")
            r = requests.post(
                f"{API_URL}/repos/{REPO}/issues/{command['issue_number']}/comments",
                headers=headers,
                json={"body": comment}
            )
            r.raise_for_status()
            result = "✅ Comment added."

        else:
            result = f"❌ Unknown action: {action}"

    except Exception as e:
        result = f"❌ Error processing command: {str(e)}"

    # Close the issue with a result comment
    requests.post(
        f"{API_URL}/repos/{REPO}/issues/{issue_number}/comments",
        headers=headers,
        json={"body": result}
    )
    requests.patch(
        f"{API_URL}/repos/{REPO}/issues/{issue_number}",
        headers=headers,
        json={"state": "closed"}
    )

if __name__ == "__main__":
    issue = get_latest_labeled_issue()
    if issue:
        parse_and_execute(issue)
