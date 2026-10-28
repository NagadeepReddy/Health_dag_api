echo "=== RECENT OOM / CONTAINER KILLS ===" && \
journalctl -k --since "3 hours ago" --no-pager 2>/dev/null \
| grep -iE 'out of memory|oom-kill|killed process|memory cgroup' \
| tail -20 || true
