echo "=== CGROUP PROCESS LIMITS ==="
for f in /sys/fs/cgroup/pids.current /sys/fs/cgroup/pids.max /sys/fs/cgroup/pids.events; do
  if [ -r "$f" ]; then
    echo "$f: $(cat "$f")"
  fi
done

echo "=== SYSTEM PROCESS LIMITS ==="
cat /proc/sys/kernel/threads-max
cat /proc/sys/kernel/pid_max
