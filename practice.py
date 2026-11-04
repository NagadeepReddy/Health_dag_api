$dest = "$env:USERPROFILE\Downloads\PZAAS_wheels"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

py -m pip download --no-deps --only-binary=:all: `
  "einops==0.8.1" -d "$dest"

if ($LASTEXITCODE -ne 0) {
    throw "Wheel download failed"
}

$wheel = Get-ChildItem "$dest\einops-0.8.1-*.whl" |
    Select-Object -First 1

if (-not $wheel) {
    throw "Wheel not found"
}

scp "$($wheel.FullName)" `
  "sajjna8@10.119.98.21:/vzwhome/sajjna8/"

if ($LASTEXITCODE -ne 0) {
    throw "Transfer failed"
}

Write-Host "PZAAS EINOPS TRANSFER: PASS"
