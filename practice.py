echo "=== BACKGROUND RECEIVER ERRORS ==="
grep -niE 'background draining|deserialize|msgpack|socket|zmq|queue.*error|CTA REQUEST RECEIVED' \
/tmp/cta_context_test.log | tail -25
