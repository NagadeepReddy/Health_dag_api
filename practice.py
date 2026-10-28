journalctl -k --since "15 minutes ago" --no-pager \
  | grep -iE 'out of memory|oom|memory cgroup|killed process' \
  | tail -20 || true
