journalctl -k --since "30 minutes ago" --no-pager 2>/dev/null | \
grep -Ei 'out of memory|oom|killed process|memory cgroup' | \
tail -20 || true
