import json, pathlib, collections, datetime

src = pathlib.Path("dashboard/data/alerts.json")
dst = pathlib.Path("reports")
dst.mkdir(parents=True, exist_ok=True)
md = dst / "code_scanning_summary.md"

if not src.exists():
    raise SystemExit(f"Missing {src}. Run export first.")

data = json.loads(src.read_text(encoding="utf-8"))
alerts = data.get("alerts", [])
by_repo = collections.Counter(a["_repo"] for a in alerts)
by_sev  = collections.Counter((a.get("rule",{}) or {}).get("severity","unknown") for a in alerts)
by_tool = collections.Counter(((a.get("tool",{}) or {}).get("name","unknown")) for a in alerts)

lines = []
lines.append(f"# Code Scanning Summary for `{data.get('org')}`")
lines.append("")
lines.append(f"_Generated: {data.get('generated_at')}_")
lines.append("")
lines.append(f"**Total open alerts:** {len(alerts)}")
lines.append("")
lines.append("## By severity")
for k,v in by_sev.most_common():
    lines.append(f"- **{k}**: {v}")
lines.append("")
lines.append("## Top repos")
for repo,count in by_repo.most_common(20):
    lines.append(f"- {repo}: {count}")
lines.append("")
lines.append("## Tools")
for tool,count in by_tool.most_common():
    lines.append(f"- {tool}: {count}")
lines.append("")
lines.append("> Source: `dashboard/data/alerts.json`")
md.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {md}")
