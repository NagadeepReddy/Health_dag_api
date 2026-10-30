POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

PID=$(ss -H -ltnp '( sport = :8766 )' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
[ -n "$PID" ] || { echo "STOP: Server 8766 unavailable"; exit 1; }

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' "/proc/$PID/cgroup" | head -1)
[ -n "$CID" ] || { echo "STOP: Container not identified"; exit 1; }

"${POD[@]}" logs --tail 250 "$CID" 2>&1 |
awk '
{
  lines[NR]=$0
  if (index($0,"CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"))
    last=NR
}
END {
  start=last ? last : NR-80
  for(i=start;i<=NR;i++)
    if(i>0) print lines[i]
}'
