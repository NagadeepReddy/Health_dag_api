echo "=== AVAILABLE MEMORY ==="
free -h
awk '/MemAvailable:/ {printf "AVAILABLE RAM: %.2f GiB\n", $2/1048576}' /proc/meminfo

echo "=== CONTAINER MEMORY LIMIT ==="
for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current; do
  if [ -r "$f" ]; then
    echo "$f: $(cat "$f")"
  fi
done

echo "=== TOP MEMORY PROCESSES ==="
ps -eo pid,comm,rss --sort=-rss | head -12

echo "=== APPLICATION STORAGE ==="
df -h /application1
