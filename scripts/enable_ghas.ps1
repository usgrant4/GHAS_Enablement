[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
  [Parameter(Mandatory = $true)][string]$Org,
  [string]$NameFilter = '.*'
)

# Preconditions
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "gh CLI not found. Install from https://cli.github.com/" }
if (-not $env:GH_TOKEN) {
  # Allow users who have already 'gh auth login' to proceed; otherwise throw.
  $authed = (gh auth status 2>$null) -ne $null
  if (-not $authed) { throw "GH_TOKEN not set and no gh auth session found. Set GH_TOKEN or run 'gh auth login'." }
}

# Fetch repos (pagination handled by gh; adjust limit for large orgs)
$repos = gh repo list $Org --limit 1000 --json name,fullName,isArchived | ConvertFrom-Json
$regex = [regex]::new($NameFilter)

foreach ($r in $repos) {
  if ($r.isArchived) { continue }
  if (-not $regex.IsMatch($r.name)) { continue }

  $target = $r.fullName
  if ($PSCmdlet.ShouldProcess($target, "Enable GitHub Advanced Security")) {
    $payload = @{ security_and_analysis = @{ advanced_security = @{ status = "enabled" } } } | ConvertTo-Json -Depth 5
    try {
      gh api --method PATCH `
        -H "Accept: application/vnd.github+json" `
        -H "X-GitHub-Api-Version: 2022-11-28" `
        "repos/$target" `
        -d "$payload" | Out-Null
      Write-Host "Enabled GHAS for $target"
    }
    catch {
      Write-Warning "Failed to enable GHAS for $target: $($_.Exception.Message)"
    }
  } else {
    Write-Host "[DRY-RUN] Would enable GHAS for $target"
  }
}
