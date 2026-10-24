echo "=== TEST STATUS ==="
ps -eo pid,etime,args | grep '[c]ta_native_e2e_test.py' || true
echo "=== RESPONSE IDS ==="
grep -E 'CTA WORKER RESPONSE IDS|CTA HTTP FANOUT|CTA NATIVE HTTP STATUS|ERROR|Traceback' /tmp/cta_response_ids.log | tail -10
