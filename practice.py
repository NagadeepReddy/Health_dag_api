echo "=== ZMQ FAILURE DETAILS ==="
grep -n -A 15 -B 6 'zmq_queue.py' \
  /tmp/cta_context_test.log | tail -85
