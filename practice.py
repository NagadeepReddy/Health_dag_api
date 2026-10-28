printf '\n=== RECENT MEMORY KILLS ===\n'
journalctl -k --since "30 minutes ago" --no-pager 2>/dev/null \
  | grep -iE 'oom|out of memory|killed process|memory cgroup' \
  | tail -15 || true

printf '\n=== REMAINING CTA TEST PROCESSES ===\n'
ps -eo pid,ppid,stat,rss,args \
  | grep '[c]ta_native_e2e_test.py' \
  || echo "PASS: No CTA test processes"

printf '\n=== AVAILABLE RAM ===\n'
free -h
