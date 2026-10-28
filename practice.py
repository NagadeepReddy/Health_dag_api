printf '%s\n' '=== CTA TEST CONTAINER ==='
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps -a --filter name=sharp_gates \
  --format 'NAME={{.Names}} STATUS={{.Status}}'

printf '%s\n' '=== REMAINING CTA TEST PROCESSES ==='
ps -eo pid,ppid,stat,rss,args \
  | grep -E '[c]ta_native_e2e_test.py|[c]ta_spawn_worker.py' \
  | head -15

printf '%s\n' '=== AVAILABLE MEMORY ==='
awk '/MemAvailable:/ {printf "%.2f GiB\n", $2/1048576}' /proc/meminfo
