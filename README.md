# GHAS Enablement & Evidence Dashboard — Pro

Enable GitHub Advanced Security (GHAS), export Code Scanning alerts to JSON, summarize to Markdown, and render a lightweight static dashboard.

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

> Security note: ensure your PAT scopes match your needs and avoid pushing tokens to the repo.
