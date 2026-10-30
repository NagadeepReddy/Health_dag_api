POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

PID=$(ss -H -ltnp '( sport = :8765 )' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)

[ -n "$PID" ] || { echo "STOP: Original server unavailable"; exit 1; }

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' "/proc/$PID/cgroup" | head -1)

[ -n "$CID" ] || { echo "STOP: Container ID unavailable"; exit 1; }

"${POD[@]}" logs --tail 800 "$CID" 2>&1 |
grep -E 'CTA TRUE MAX BATCH-2|CTA WORKER RESPONSE IDS|CTA RESPONSE QUEUE SEND|CTA RESPONSE SOCKET RECEIVED|CTA RESPONSE ID MATCH|CTA HTTP QUEUE ITEM|CTA RESPONSE WORKER LOOP|CTA HTTP FANOUT|POST /v2/cta/predict|Traceback|ERROR' |
tail -65
