echo "=== TEST STATUS ==="
ps -eo pid,etime,args | grep '[c]ta_native_e2e_test.py' || true

echo "=== REQUEST TRACE ==="
tail -n 20 /tmp/cta_request_trace.log
