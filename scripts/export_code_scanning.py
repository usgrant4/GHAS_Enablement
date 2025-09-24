import os, json, requests, time
ORG = os.getenv("GH_ORG"); TOKEN = os.getenv("GH_TOKEN")
API = "https://api.github.com"
HDRS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

def paged(url):
    while url:
        r = requests.get(url, headers=HDRS, timeout=30)
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")

repos = [r for r in paged(f"{API}/orgs/{ORG}/repos?per_page=100")]
rollup = []
for r in repos:
    alerts_url = f"{API}/repos/{ORG}/{r['name']}/code-scanning/alerts?per_page=100&state=open"
    for a in paged(alerts_url):
        rollup.append({
            "repo": r["name"],
            "rule_id": a.get("rule", {}).get("id"),
            "severity": a.get("rule", {}).get("severity"),
            "tool": a.get("tool", {}).get("name"),
            "created_at": a.get("created_at"),
            "html_url": a.get("html_url"),
            "state": a.get("state"),
        })
    time.sleep(0.2)

os.makedirs("dashboard/data", exist_ok=True)
with open("dashboard/data/alerts.json", "w", encoding="utf-8") as f:
    json.dump(rollup, f, indent=2)
print(f"Exported {len(rollup)} alerts.")
