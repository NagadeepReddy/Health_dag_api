journalctl -k -b --no-pager | grep -Ei 'oom|out of memory|killed process|memory cgroup' | tail -20
