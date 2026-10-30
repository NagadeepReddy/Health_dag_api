POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766

echo "=== NEW BATCH-2 CONTAINER ==="
STATE=$("${POD[@]}" inspect "$NAME" --format '{{.State.Status}}') || exit 1
"${POD[@]}" inspect "$NAME" --format 'STATE={{.State.Status}} EXIT={{.State.ExitCode}} OOM={{.State.OOMKilled}}'

echo "=== STARTUP LOGS ==="
"${POD[@]}" logs --tail 100 "$NAME" 2>&1

echo "=== NATIVE HTTP HEALTH ==="
if [ "$STATE" = "running" ]; then
  python3 - <<'PY'
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8766/health", timeout=5) as r:
        print("HTTP HEALTH:", r.status)
        print("BODY:", r.read(500).decode(errors="replace"))
except Exception as e:
    print("HEALTH NOT READY:", repr(e))
PY
else
  echo "STOP: Container exited; inspect startup error above."
fi

echo "ORIGINAL DS/MAX: NOT MODIFIED"
