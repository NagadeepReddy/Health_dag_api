$ErrorActionPreference = "Stop"
$dest = "$env:USERPROFILE\Downloads\PZAAS_wheels"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

py -m pip download --only-binary=:all: --no-deps `
  --platform manylinux2014_x86_64 `
  --python-version 312 `
  --implementation cp --abi cp312 `
  joblib scikit-learn -d "$dest"

if ($LASTEXITCODE -ne 0) {
    throw "Wheel download failed"
}

Get-ChildItem "$dest\*.whl" |
Where-Object { $_.Name -match '^(joblib|scikit_learn)-' } |
ForEach-Object {
    scp $_.FullName "sajjna8@10.119.98.21:/vzwhome/sajjna8/"
    if ($LASTEXITCODE -ne 0) {
        throw "Transfer failed"
    }
}

Write-Host "PZAAS DEPENDENCY TRANSFER: PASS"
