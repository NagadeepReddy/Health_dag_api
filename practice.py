cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_max_true_batch_dev_20261028/native_concurrent2_timeout_trace.log

if [ ! -f "$LOG" ]; then
  echo "STOP: Diagnostic log missing"
else
  echo "=== REQUEST AND QUEUE EVENTS ==="
  grep -nEi \
    'REQUEST [12]:|CTA HTTP QUEUE ITEM|CTA RESPONSE QUEUE|REQUEST ID|RequestID|CTA PREDICT|CTA TIMEOUT TRACEBACK|CTA RESPONSE WORKER|CTA QUEUE|cancelled|timed out|HTTP 504' \
    "$LOG" | tail -65

  echo "=== EVENT COUNTS ==="
  printf "Response queue sends: "
  grep -c 'CTA RESPONSE QUEUE SEND: COMPLETED' "$LOG" || true

  printf "Timeout tracebacks: "
  grep -c 'CTA TIMEOUT TRACEBACK' "$LOG" || true

  echo "CHECK COMPLETE — NO CHANGES"
fi
