import os, sys, json, time, requests, math, pathlib

ORG = os.environ.get("GH_ORG") or sys.argv[1] if len(sys.argv)>1 else None
TOKEN = os.environ.get("GH_TOKEN")

if not ORG:
    raise SystemExit("GH_ORG env var (or argv[1]) is required")
if not TOKEN:
    raise SystemExit("GH_TOKEN env var is required")

S = requests.Session()
S.headers.update({
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})

def paged(url, params=None):
    params = dict(params or {})
    params.setdefault("per_page", 100)
    page = 1
    while True:
        params["page"] = page
        r = S.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data: break
        yield from data
        if "next" not in r.links: break
        page += 1

def list_repos(org):
    url = f"https://api.github.com/orgs/{org}/repos"
    return [r for r in paged(url)]

def list_alerts(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/code-scanning/alerts"
    return [a for a in paged(url, params={"state":"open"})]

def main():
    out_dir = pathlib.Path("dashboard/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    all_alerts = []
    repos = list_repos(ORG)
    for r in repos:
        if r.get("archived"): 
            continue
        full_name = r["full_name"]
        owner, name = full_name.split("/",1)
        alerts = list_alerts(owner, name)
        for a in alerts:
            a["_repo"] = full_name
        all_alerts.extend(alerts)

    payload = {
        "org": ORG,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(all_alerts),
        "alerts": all_alerts,
    }
    out_path = out_dir / "alerts.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} with {len(all_alerts)} alerts")

if __name__ == "__main__":
    main()
