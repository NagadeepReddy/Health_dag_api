printf '\n=== AVAILABLE MEMORY ===\n'
free -h

printf '\n=== TOP 10 MEMORY PROCESSES ===\n'
ps -eo pid,ppid,rss,stat,comm --sort=-rss | head -11

printf '\n=== RECENT OOM EVENTS ===\n'
journalctl -k --since "10 minutes ago" --no-pager 2>/dev/null \
  | grep -iE 'out of memory|oom-kill|killed process' \
  | tail -5 || true
