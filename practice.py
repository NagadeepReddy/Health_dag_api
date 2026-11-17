Select-String -Path .\helm-chart\dev\values.yaml -Pattern '^\s*(ingress:|host:|path:)' -Context 0,2
