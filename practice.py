POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766-10g

echo "=== CONTAINER STATUS ==="
"${POD[@]}" inspect "$NAME" --format \
'STATE={{.State.Status}} OOM={{.State.OOMKilled}} STARTED={{.State.StartedAt}}'

echo "=== ACTUAL MEMORY ==="
"${POD[@]}" exec "$NAME" sh -c '
for f in /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.events; do
  echo "$f"
  cat "$f"
done
' 2>&1

echo "=== PROCESS STATUS ==="
"${POD[@]}" top "$NAME" 2>&1 | head -30

echo "=== CURRENT HTTP STATUS ==="
python3 - <<'PY'
import urllib.request
try:
    with urllib.request.urlopen(
        "http://127.0.0.1:8766/health", timeout=5
    ) as r:
        print("HEALTH:", r.status)
        print("BODY:", r.read(500).decode(errors="replace"))
except Exception as e:
    print("HEALTH FAILED:", repr(e))
PY

echo "=== UNFILTERED STARTUP LOGS ==="
"${POD[@]}" logs --tail 130 "$NAME" 2>&1

echo "ORIGINAL DS/MAX: UNCHANGED"
