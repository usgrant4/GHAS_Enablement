[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
  [Parameter(Mandatory=$true)][string]$Org,
  [string]$NameFilter = '.*',
  [switch]$WhatIf
)
if (-not $env:GH_TOKEN) { throw "GH_TOKEN not set" }
$repos = gh api -H "Authorization: token $env:GH_TOKEN" "/orgs/$Org/repos?per_page=100" | ConvertFrom-Json
$filter = New-Object System.Text.RegularExpressions.Regex($NameFilter)
foreach ($r in $repos) {
  if (-not $filter.IsMatch($r.name)) { continue }
  $payload = @{ security_and_analysis = @{ advanced_security = @{ status = "enabled" } } } | ConvertTo-Json
  if ($WhatIf) {
    Write-Host "[DRY-RUN] Would enable GHAS for $($r.full_name)"
  } else {
    Write-Host "[DRY-RUN] Would enable GHAS for $target"
  }
}
