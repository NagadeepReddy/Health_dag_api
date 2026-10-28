echo "=== LAST MAX EXECUTION STAGE ==="
grep -nE 'CTA REQUEST RECEIVED|CTA MODEL LOAD|CTA preprocess|CTA PREDICT_RAW|MAX GRAPH|MAX INFERENCE|COMPILING|REGISTRY|EXECUTING REAL|MAX INFERENCE EXECUTED|CTA RESPONSE|CTA STATUS|Timeout|Traceback|Exception|Error' \
/application1/cta_compile_retry_1028.log | tail -35

echo "=== CONTAINER MEMORY KILLS ==="
journalctl -k --since "15 minutes ago" --no-pager 2>/dev/null \
| grep -iE 'oom|killed process|memory cgroup' | tail -10 || true

echo "=== REMAINING CTA PROCESSES ==="
ps -eo pid,ppid,stat,args \
| grep '[c]ta_native_e2e_test.py' \
|| echo "PASS: No CTA test processes"
