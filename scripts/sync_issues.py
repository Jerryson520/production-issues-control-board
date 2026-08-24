#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
GITLAB_REPO = ROOT.parent / "production-issues"
PROJECT_ID = "2308"

raw = subprocess.run(
    ["glab", "api", f"projects/{PROJECT_ID}/issues?per_page=100"],
    cwd=GITLAB_REPO,
    check=True,
    capture_output=True,
    text=True,
).stdout

workflow_names = {
    "inbox": "Inbox", "needs-context": "Needs Context", "triage": "Triage",
    "investigating": "Investigating", "handed-off": "Handed Off",
    "verifying": "Verifying", "resolved": "Resolved",
}

issues = []
for item in json.loads(raw):
    labels = item.get("labels", [])
    module = item["title"].split("]", 1)[0].lstrip("[") if item["title"].startswith("[") else "未分类"
    title = item["title"].split("]", 1)[1].strip() if item["title"].startswith("[") and "]" in item["title"] else item["title"]
    workflow = next((x.split("::", 1)[1] for x in labels if x.startswith("workflow::")), "inbox")
    severity = next((x.split("::", 1)[1].upper() for x in labels if x.startswith("severity::")), "—")
    source = next((x.split("::", 1)[1].title() for x in labels if x.startswith("source::")), "Unknown")
    updated = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Shanghai"))
    issues.append({
        "iid": item["iid"], "title": title, "module": module,
        "state": "closed" if item["state"] == "closed" else "open",
        "flow": workflow_names.get(workflow, workflow.replace("-", " ").title()),
        "severity": severity, "source": source,
        "author": item.get("author", {}).get("name") or item.get("author", {}).get("username") or "Unknown",
        "updated": updated.strftime("%Y-%m-%d %H:%M"), "web_url": item["web_url"],
    })

generated = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M CST")
output = {"generated_at": generated, "issues": issues}
(ROOT / "public" / "issues.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(f"synced {len(issues)} issues at {generated}")
