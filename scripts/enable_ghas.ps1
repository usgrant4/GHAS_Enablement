[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
  [Parameter(Mandatory = $true)][string]$Org,
  [string]$NameFilter = '.*'
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "gh CLI not found. Install from https://cli.github.com/" }

# Prefer existing gh auth; if not, require GH_TOKEN env
$hasAuth = $false
try { gh auth status | Out-Null; $hasAuth = $true } catch { $hasAuth = $false }
if (-not $hasAuth -and -not $env:GH_TOKEN) { throw "No gh auth session and GH_TOKEN not set. Run 'gh auth login' or set GH_TOKEN." }

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
    } catch {
      Write-Warning "Failed to enable GHAS for $target: $($_.Exception.Message)"
    }
  } else {
    Write-Host "[DRY-RUN] Would enable GHAS for $target"
  }
}
