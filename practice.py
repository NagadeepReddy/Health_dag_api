POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

PID=$(ss -H -ltnp '( sport = :8766 )' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' "/proc/$PID/cgroup" | head -1)

if [ -n "$CID" ]; then
  "${POD[@]}" logs --tail 400 "$CID" 2>&1 |
    grep -E 'CTA TRUE MAX BATCH-2|CTA RESPONSE SOCKET RECEIVED|CTA RESPONSE ID MATCH|CTA HTTP QUEUE ITEM|CTA WORKER RESPONSE IDS|CTA RESPONSE QUEUE SEND|CTA RESPONSE WORKER LOOP|POST /v2/cta/predict|Gateway Timeout' |
    tail -45
else
  echo "STOP: Optimized container not identified"
fi
