printf '%s\n' '=== RECENT MEMORY ERRORS ==='
journalctl -k --since "10 minutes ago" --no-pager 2>/dev/null \
  | grep -iE 'out of memory|oom|killed process|memory cgroup' \
  | tail -10 || true

printf '%s\n' '=== REMAINING CTA/MAX PROCESSES ==='
ps -eo pid,ppid,stat,etime,rss,args \
  | grep -E '[c]ta_native_e2e_test|[c]ta_spawn_worker|[m]axserve_cta_extension|[p]odman.*run' \
  | head -15

printf '%s\n' '=== AVAILABLE MEMORY ==='
awk '/MemAvailable:/ {printf "Available RAM: %.2f GiB\n", $2/1048576}' /proc/meminfo
