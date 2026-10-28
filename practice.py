echo "=== RESPONSE WORKER DIAGNOSTICS ==="
grep -nEi \
'response.worker|fanout|queue item|queue send|task exception|connection|zmq|traceback|timeout|cancelled|broken pipe|killed|error' \
/application1/cta_queue_fix_retry.log | tail -45
