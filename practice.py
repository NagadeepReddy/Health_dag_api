echo "=== TEST PROCESS ==="
ps -eo pid,ppid,stat,etime,args | grep -E '[c]ta_native_e2e_test.py|[t]imeout 50s podman'

echo "=== LAST RESULTS ==="
grep -E 'CTA MAX REQUEST UNWRAPPED|CTA REQUEST RECEIVED|CTA WORKER RESPONSE IDS|CTA NATIVE HTTP STATUS|KeyError|TypeError|Error|Traceback|EXIT CODE' \
/tmp/cta_queue_fix_test.log | tail -20
