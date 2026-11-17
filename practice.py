[xml]$s = Get-Content .\settings.xml -Raw
$s.settings.servers.server | ForEach-Object {
  "Server configured: $([bool]$_.id); Password configured: $([bool]$_.password)"
}
