Get-ChildItem .\helm-chart\dev -Recurse -File |
Select-String -Pattern 'host:|hosts:|ingress' |
Select-Object -First 20
