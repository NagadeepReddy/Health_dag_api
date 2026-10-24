echo "=== TEST PROCESS ==="
ps -eo pid,etime,args | grep '[c]ta_native_e2e_test.py' || true

echo "=== LATEST RESULT ==="
tail -n 15 /tmp/cta_queue_init.log
