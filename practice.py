journalctl -k --since "15 minutes ago" --no-pager 2>/dev/null | grep -Ei 'oom|out of memory|killed process|memory cgroup' | tail -15
