# GHAS Enablement & Evidence Dashboard

Automate enabling **GitHub Advanced Security (GHAS)** across repositories and export **Code Scanning** alerts to a JSON roll‑up, Markdown summary, and a lightweight static dashboard.

[![CI – Export Alerts](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/export-alerts.yml?branch=main)](https://github.com/OWNER/REPO/actions/workflows/export-alerts.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![PowerShell](https://img.shields.io/badge/PowerShell-7+-5391FE)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

> Replace `OWNER/REPO` above with your repository path.

---

## What this delivers

- **Org‑wide enablement** of GHAS (opt‑in via regex filter, dry‑run supported).
- **Nightly export** of Code Scanning alerts → `dashboard/data/alerts.json` + `reports/code_scanning_summary.md`.
- **Static dashboard** (`dashboard/index.html`) for quick at‑a‑glance status by repo/severity/rule.
- **GitHub Actions** workflows for on‑demand enablement and scheduled exports.

---

## Repo layout

```text
ghas-enablement-and-evidence-dashboard/
├─ .github/workflows/
│  ├─ enable-ghas.yml         # Manual run to enable GHAS
│  └─ export-alerts.yml       # Nightly export + commit JSON/Markdown
├─ scripts/
│  ├─ enable_ghas.ps1         # Enable GHAS for matching repos
│  ├─ export_code_scanning.py  # Export alerts to JSON
│  └─ summarize_alerts.py      # Create Markdown summary
├─ dashboard/
│  ├─ index.html               # Static table reading data/alerts.json
│  └─ data/alerts.json         # (generated) roll‑up
└─ reports/
   └─ code_scanning_summary.md # (generated) summary
```

---

## Prerequisites

- A **PAT** or **GitHub App** token with scopes: `repo`, `security_events`, `admin:org` (for enablement).
- Set the following **repository secrets**:
  - `GH_TOKEN` – PAT/App token
  - `GH_ORG` – your GitHub organization name
- (Optional, for local PowerShell) Install the [GitHub CLI](https://cli.github.com/) and sign in: `gh auth login`.

> For GitHub App, exchange the app token to an installation token and pass that via `GH_TOKEN` in the workflow.

---

## Workflows

### 1) Enable GHAS (manual)

`.github/workflows/enable-ghas.yml`

- Triggered via **Actions → Run workflow**.
- Inputs:
  - `name_filter` – regex to select repos (default: `.*`)
  - `dry_run` – `"true"` (default) or `"false"`

This calls `scripts/enable_ghas.ps1`, which PATCHes each matched repo’s `security_and_analysis.advanced_security` to `enabled`.
Dry‑run prints what would be enabled without patching.

### 2) Export Alerts (scheduled + manual)

`.github/workflows/export-alerts.yml`

- **Scheduled (cron)** nightly, and **workflow_dispatch** for manual runs.
- Steps:
  1. Run `scripts/export_code_scanning.py` to pull open Code Scanning alerts across the org.
  2. Generate `reports/code_scanning_summary.md` via `scripts/summarize_alerts.py`.
  3. Commit updated `dashboard/data/alerts.json` and `reports/code_scanning_summary.md` to the repo.

---

## Local usage (optional)

PowerShell (dry run, enable repos starting with `sample-`):
```powershell
$env:GH_TOKEN = "<token>"
$env:GH_ORG   = "<org>"
pwsh ./scripts/enable_ghas.ps1 -Org $env:GH_ORG -NameFilter '^sample-' -WhatIf
```

Python (export alerts into local working copy):
```bash
python -m pip install --upgrade pip requests
GH_TOKEN=<token> GH_ORG=<org> python scripts/export_code_scanning.py
python scripts/summarize_alerts.py
# Open dashboard locally (file://...), the table reads dashboard/data/alerts.json
```

---

## Dashboard

Open `dashboard/index.html` (via GitHub Pages or locally). It loads `dashboard/data/alerts.json` and renders a simple table:

- **Columns**: repo, severity, rule, tool, link
- **Sources**: all repos in the org matching GHAS Code Scanning alerts (state=open)
- **Updates**: on each `export-alerts.yml` run

> To publish with **GitHub Pages**, set Pages to serve from `/ (root)`. The `dashboard/` folder is static assets committed to `main`.

---

## Security considerations

- Store tokens in **repository secrets** (not in code).  
- Restrict PAT/App permissions to the **least privileges** needed.  
- If your org enforces GHAS billing per repo, test with dry‑run first.  
- Consider scoping enablement to a repo allow‑list instead of regex.

---

## Troubleshooting

- **403 / insufficient scopes** – token lacks `admin:org` or repo admin. Use an org admin token/GitHub App.  
- **No alerts exported** – ensure repos have code scanning tools configured (CodeQL or third‑party).  
- **Rate limits** – the exporter paginates and throttles lightly; for very large orgs, run less frequently or shard by repo name.  
- **Git push errors** – Actions needs permission to push to `main`. Consider a docs/data branch or `permissions: contents: write` in the workflow.

---

## Example snippets

PowerShell (core loop in `enable_ghas.ps1`):
```powershell
$repos = gh api -H "Authorization: token $env:GH_TOKEN" "/orgs/$Org/repos?per_page=100" | ConvertFrom-Json
foreach ($r in $repos) {
  if (-not $filter.IsMatch($r.name)) { continue }
  $payload = @{ security_and_analysis = @{ advanced_security = @{ status = "enabled" } } } | ConvertTo-Json
  if ($WhatIf) { Write-Host "[DRY-RUN] Would enable GHAS for $($r.full_name)" }
  else { gh api -X PATCH -H "Authorization: token $env:GH_TOKEN" "/repos/$($r.full_name)" -F "security_and_analysis=$payload" | Out-Null }
}
```

Python (exporter core in `export_code_scanning.py`):
```python
def paged(url):
    while url:
        r = requests.get(url, headers=HDRS, timeout=30)
        r.raise_for_status()
        yield from r.json()
        url = r.links.get("next", {}).get("url")
```

---

## License & Author

MIT — feel free to copy and adapt.

**Ulysses Grant, IV**  
[LinkedIn](https://www.linkedin.com/in/usgrant4/) 
[GitHub](https://github.com/usgrant4)

---