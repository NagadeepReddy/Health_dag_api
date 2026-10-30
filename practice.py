POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-importfirst-8766

echo "=== CONTAINER AND MEMORY LIMIT ==="
"${POD[@]}" inspect "$NAME" --format \
'STATE={{.State.Status}} EXIT={{.State.ExitCode}} OOM={{.State.OOMKilled}} MEMORY_LIMIT_BYTES={{.HostConfig.Memory}}'

echo "=== WORKER PROCESSES ==="
"${POD[@]}" top "$NAME" pid ppid comm 2>&1 || true

echo "=== MEMORY FAILURE COUNTERS ==="
"${POD[@]}" exec "$NAME" sh -c '
for f in /sys/fs/cgroup/memory.events /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.max; do
  if [ -r "$f" ]; then
    echo "$f"
    cat "$f"
  fi
done
' 2>&1 || true

echo "=== FIRST WORKER ERRORS WITH FULL CONTEXT ==="
"${POD[@]}" logs --tail 1800 "$NAME" 2>&1 | python3 -c '
import sys,re
lines=sys.stdin.read().splitlines()
pattern=re.compile(
 r"Traceback|Exception:|Error:|Worker failed|OOM|"
 r"out of memory|Killed|Segmentation|Failed to create",
 re.I
)
hits=[i for i,s in enumerate(lines) if pattern.search(s)]
selected=[]
for i in hits:
    if not selected or i-selected[-1]>25:
        selected.append(i)
    if len(selected)==3:
        break
print("ERROR EVENTS:",len(hits))
for i in selected:
    print("\n--- ERROR CONTEXT AT LOG LINE",i+1,"---")
    for s in lines[max(0,i-15):min(len(lines),i+30)]:
        print(s[:1000])
print("\n=== LAST 20 LOG LINES ===")
for s in lines[-20:]:
    print(s[:1000])
'

echo "=== READ-ONLY DIAGNOSIS COMPLETE ==="
