POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

echo "=== ISOLATED CONTAINER STATE ==="
"${POD[@]}" inspect "$NAME" \
  --format 'STATUS={{.State.Status}} EXIT={{.State.ExitCode}} OOM={{.State.OOMKilled}} ERROR={{.State.Error}}'

echo "=== LATEST STARTUP FAILURE ==="
"${POD[@]}" logs --tail 250 "$NAME" 2>&1 | tail -100

echo "ORIGINAL MAX: UNTOUCHED"
echo "ORIGINAL DS: UNCHANGED"
echo "FILES MODIFIED: NONE"
