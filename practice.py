echo "=== THREAD RESOURCE CHECK ==="
echo "Current threads: $(ps -eLf --no-headers | wc -l)"
echo "User process limit: $(ulimit -u)"
echo "System thread limit: $(cat /proc/sys/kernel/threads-max)"
echo "Cgroup: $(cat /proc/self/cgroup)"
for f in /sys/fs/cgroup/pids.current /sys/fs/cgroup/pids.max /sys/fs/cgroup/pids.events; do
  if [ -r "$f" ]; then
    echo "=== $f ==="
    cat "$f"
  fi
done
echo "Available memory:"
free -h
echo "FILES MODIFIED: NONE"
echo "MAX STARTED: NO"
