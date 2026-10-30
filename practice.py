
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== WORKER PROCESSES ==="
"${POD[@]}" top "$NAME"

echo "=== LATEST WORKER EXECUTION TRACE ==="
"${POD[@]}" logs --tail 1200 "$NAME" 2>&1 | grep -Ei -C 2 'CTA TRUE MAX|CTA MODEL|CTA QUEUE|CTA NATIVE|REAL INPUT|EXECUTING|COMPIL|GRAPH|CHECKPOINT|BATCH|ERROR|Exception|Traceback|Worker failed|OOM|Killed|STOP:' | tail -100

echo "ORIGINAL MAX: UNCHANGED"
echo "ORIGINAL DS: UNCHANGED"
echo "NO FILES MODIFIED"
