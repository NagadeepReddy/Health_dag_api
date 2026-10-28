printf '\n=== CTA CONTAINERS STILL RUNNING ===\n'
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps --format '{{.Names}} {{.Status}}' \
  | grep -E 'eloquent_ishizaka|strange_pascal|priceless_volhard|musing_wu|sharp_gates' \
  || echo "PASS: No identified CTA test containers running"

printf '\n=== REMAINING CTA PROCESSES ===\n'
ps -eo pid,ppid,stat,rss,args \
  | grep '[c]ta_native_e2e_test.py' \
  || echo "PASS: No CTA test processes"

printf '\n=== AVAILABLE RAM ===\n'
awk '/MemAvailable:/ {printf "%.2f GiB\n", $2/1048576}' /proc/meminfo
