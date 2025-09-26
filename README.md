# GHAS Enablement & Evidence Dashboard — Pro

Automate enabling **GitHub Advanced Security (GHAS)** across repositories and export **Code Scanning** alerts to a JSON roll‑up, Markdown summary, and a lightweight static dashboard.

[![CI – Export Alerts](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/export-alerts.yml?branch=main)](https://github.com/OWNER/REPO/actions/workflows/export-alerts.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![PowerShell](https://img.shields.io/badge/PowerShell-7+-5391FE)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## What’s in this repo

```
scripts/
  enable_ghas.ps1              # Enable GHAS across org repos (regex filter, supports -WhatIf)
  export_code_scanning.py      # Export open Code Scanning alerts → dashboard/data/alerts.json
  summarize_alerts.py          # Create reports/code_scanning_summary.md

dashboard/
  data/alerts.json             # Exported data consumed by the static dashboard

.github/workflows/
  export-alerts.yml            # Manual export/summarize pipeline (schedule commented for public repos)
  enable-ghas.yml              # Manual GHAS enablement runner (invokes the PowerShell script)

index.html                     # Static dashboard that reads dashboard/data/alerts.json
```

## Setup (public repo safe)

1. **Secrets**
   - `GH_TOKEN` — fine‑grained PAT with `security_events:read`, `contents:read`, `metadata:read` (and **repo:admin** if enabling GHAS).
   - `GH_ORG` — your organization login (e.g., `my-org`).

2. **Optional GH auth**  
   Instead of `GH_TOKEN`, you may `gh auth login` locally when using the PowerShell script.

---

## Workflows

### Export alerts (manual)

`.github/workflows/export-alerts.yml` runs on **manual dispatch**. The cron schedule is **commented out** to avoid noisy/public automation. It:

- checks out with full history (`fetch-depth: 0`)
- installs Python + `requests`
- runs `scripts/export_code_scanning.py` and `scripts/summarize_alerts.py`
- commits `dashboard/data/alerts.json` and `reports/code_scanning_summary.md` (only from `main`)
- uploads both files as workflow artifacts

### Enable GHAS (manual)

`.github/workflows/enable-ghas.yml` exposes two inputs: `org` and `name_filter`. It calls the PowerShell script with **`-WhatIf`** by default. Remove `-WhatIf` to enact changes.

---

## Scripts

### `scripts/enable_ghas.ps1`

- Mass‑friendly: uses `gh repo list ... --json` (no `jq` needed), supports `-WhatIf` via `SupportsShouldProcess`.
- Skips archived repos; regex filter via `-NameFilter`.
- Sends proper JSON payload to `PATCH /repos/{owner}/{repo}`:

```jsonc
{ "security_and_analysis": { "advanced_security": { "status": "enabled" } } }
```

### `scripts/export_code_scanning.py`

- Paginates org repos and each repo’s **open** Code Scanning alerts.
- Produces `dashboard/data/alerts.json` with a flat `alerts[]` array and metadata (`org`, `generated_at`, `count`).

### `scripts/summarize_alerts.py`

- Summarizes by **severity**, **repo**, and **tool**, producing `reports/code_scanning_summary.md`.

### `index.html`

- Minimal, dependency‑free dashboard that fetches `dashboard/data/alerts.json` and renders a table + quick stats.
- Works with GitHub Pages or a static host.

---

## Changes made in this update

- **Workflows**
  - Added `permissions: contents: write` and `concurrency` to `export-alerts.yml`.
  - Commented out the cron schedule for public‑repo friendliness.
  - Added branch‑safe commit/push logic and artifact upload.
  - New `enable-ghas.yml` with typed inputs and a default **dry‑run** (`-WhatIf`).

- **Scripts**
  - Replaced placeholders with functional implementations:
    - `enable_ghas.ps1`: robust, paginated, `-WhatIf`, regex filter, archived‑repo skip.
    - `export_code_scanning.py`: paginated export, consolidated JSON.
    - `summarize_alerts.py`: Markdown rollup with key breakdowns.

- **Dashboard**
  - Replaced placeholder `index.html` with a simple viewer wiring to `dashboard/data/alerts.json`.

- **Repo hygiene**
  - No schedules by default, no secrets hard‑coded, and outputs are committed only when changed.
  - Artifacts are uploaded for download from each run.

---

## Usage

- **Enable GHAS (dry‑run)**
  - Actions → *enable-ghas* → Run workflow (inputs: `org`, optional `name_filter`).
  - Remove `-WhatIf` in the workflow step to actually enable.

- **Export alerts + summary**
  - Actions → *export-alerts* → Run workflow.
  - Find artifacts in the run summary or check committed files on `main`.

---

## Local development

```bash
# Export (requires GH_TOKEN and GH_ORG)
export GH_TOKEN=... GH_ORG=my-org
python scripts/export_code_scanning.py
python scripts/summarize_alerts.py
open index.html  # or use a static server
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
