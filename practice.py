$ErrorActionPreference = "Stop"
$dest = "$env:USERPROFILE\Downloads\PZAAS_wheels"

py -m pip download --no-deps --only-binary=:all: `
  --platform manylinux2014_x86_64 `
  --python-version 312 `
  --implementation cp --abi cp312 `
  "scikit-learn==1.6.1" -d "$dest"

if ($LASTEXITCODE -ne 0) {
    throw "Download failed"
}

$wheel = Get-ChildItem "$dest\scikit_learn-1.6.1-*.whl" |
    Select-Object -First 1

if (-not $wheel) {
    throw "Wheel not found"
}

scp "$($wheel.FullName)" `
  "sajjna8@10.119.98.21:/vzwhome/sajjna8/"

if ($LASTEXITCODE -ne 0) {
    throw "Transfer failed"
}

Write-Host "PZAAS SKLEARN 1.6.1 TRANSFER: PASS"
