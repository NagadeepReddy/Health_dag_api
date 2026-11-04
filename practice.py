$ErrorActionPreference = "Stop"
$dest = "$env:USERPROFILE\Downloads\PZAAS_wheels"

py -m pip download --no-deps --only-binary=:all: `
  --platform manylinux2014_x86_64 `
  --python-version 312 `
  --implementation cp --abi cp312 `
  "threadpoolctl>=3.2,<4" "scipy>=1.8,<2" `
  -d "$dest"

if ($LASTEXITCODE -ne 0) {
    throw "Dependency download failed"
}

$wheels = Get-ChildItem "$dest\*.whl" |
    Where-Object { $_.Name -match '^(threadpoolctl|scipy)-' }

if ($wheels.Count -lt 2) {
    throw "Required wheels missing"
}

foreach ($wheel in $wheels) {
    scp "$($wheel.FullName)" `
      "sajjna8@10.119.98.21:/vzwhome/sajjna8/"

    if ($LASTEXITCODE -ne 0) {
        throw "Transfer failed: $($wheel.Name)"
    }
}

Write-Host "PZAAS RUNTIME DEPENDENCIES: TRANSFER PASS"
