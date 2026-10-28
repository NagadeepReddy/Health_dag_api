echo "=== LAST MAX RUN ==="
grep -nE 'CTA MODEL LOAD|CTA preprocess|MAX GRAPH|ENGINE|Timeout|Killed|Error|Exception' \
/application1/cta_final_diag_1028.log | tail -35

echo "=== KERNEL MEMORY KILLS ==="
journalctl -k --since "2026-10-28 00:00:00" --no-pager 2>/dev/null \
| grep -iE 'oom-kill|out of memory|killed process|memory cgroup' \
| tail -15 || true
