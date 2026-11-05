
$ErrorActionPreference = "Stop"

$dest = Join-Path $env:USERPROFILE "Downloads\pzaas_apscheduler_wheels"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Host "=== DOWNLOAD PZAAS LINUX WHEELS ==="

py -3 -m pip download `
  --only-binary=:all: `
  --platform manylinux2014_x86_64 `
  --python-version 3.12 `
  --implementation cp `
  --abi cp312 `
  --dest $dest `
  "APScheduler>=3,<4"

if ($LASTEXITCODE -ne 0) {
    throw "Download failed. Check approved package source."
}

$wheels = @(Get-ChildItem $dest -Filter "*.whl" -File)

if (-not ($wheels.Name -match "^APScheduler-3\.")) {
    throw "APScheduler 3.x wheel missing"
}

Write-Host "=== TRANSFER WHEELS TO VM ==="

ssh sajjna8@10.119.98.21 "mkdir -p /vzwhome/sajjna8/pzaas_wheels"

if ($LASTEXITCODE -ne 0) {
    throw "Remote directory creation failed"
}

foreach ($wheel in $wheels) {
    scp $wheel.FullName "sajjna8@10.119.98.21:/vzwhome/sajjna8/pzaas_wheels/"

    if ($LASTEXITCODE -ne 0) {
        throw "Transfer failed: $($wheel.Name)"
    }
}

Write-Host "PZAAS APSCHEDULER WHEELS TRANSFERRED: PASS"
Write-Host "NEXT: INSTALL OFFLINE IN ISOLATED PZAAS IMAGE"
