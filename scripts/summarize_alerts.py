import json, collections, os
data = json.load(open("dashboard/data/alerts.json"))
by_repo = collections.Counter([d["repo"] for d in data])
by_sev  = collections.Counter([d.get("severity") or "unknown" for d in data])
lines = ["# Code Scanning Summary", "", "## By Repo"]
for k,v in by_repo.most_common(): lines.append(f"- {k}: {v}")
lines += ["", "## By Severity"]
for k,v in by_sev.most_common(): lines.append(f"- {k}: {v}")
os.makedirs("reports", exist_ok=True)
open("reports/code_scanning_summary.md", "w").write("\n".join(lines))
print("Wrote reports/code_scanning_summary.md")
