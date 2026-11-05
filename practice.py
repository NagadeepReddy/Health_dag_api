
$ErrorActionPreference = "Stop"

$dest = Join-Path $env:USERPROFILE "Downloads\pzaas_sklearn161"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Host "=== DOWNLOAD MATCHING SCIKIT-LEARN 1.6.1 ==="

py -3 -m pip download `
  --only-binary=:all: `
  --no-deps `
  --platform manylinux2014_x86_64 `
  --python-version 3.12 `
  --implementation cp `
  --abi cp312 `
  --dest $dest `
  "scikit-learn==1.6.1"

if ($LASTEXITCODE -ne 0) {
    throw "Download failed"
}

$wheel = Get-ChildItem -Path $dest -Filter "scikit_learn-1.6.1-*.whl" -File |
    Select-Object -First 1

if (-not $wheel) {
    throw "Matching wheel not found"
}

scp $wheel.FullName "sajjna8@10.119.98.21:/vzwhome/sajjna8/pzaas_wheels/"

if ($LASTEXITCODE -ne 0) {
    throw "Transfer failed"
}

Write-Host "PZAAS SCIKIT-LEARN 1.6.1 TRANSFER: PASS"
Write-Host "CTA/BPLAN IMAGE: UNCHANGED"
