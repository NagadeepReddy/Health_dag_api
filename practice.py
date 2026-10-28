echo "=== AVAILABLE MEMORY ==="
free -h

echo "=== MEMORY PRESSURE ==="
cat /proc/pressure/memory

echo "=== TOP MEMORY CONSUMERS ==="
ps -eo pid,comm,rss --sort=-rss | head -12

echo "=== SAFE TO RUN MAX? ==="
awk '/MemAvailable:/ {
  printf "Available: %.1f GiB\n", $2/1048576
  print ($2 >= 16777216 ? "MEMORY CHECK: PASS" : "MEMORY CHECK: BLOCKED")
}' /proc/meminfo
