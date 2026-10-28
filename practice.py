cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
LOG=/application1/cta_native_alignment_validation.log

echo "=== COMPLETE REQUEST / RESPONSE TIMELINE ==="
grep -nEi \
'CTA ROUTES|WORKER STARTUP|CTA PROBE|CTA ROUTE|CTA ACTIVE RECEIVER|CTA HTTP|CTA RECEIVER|CTA QUEUE|CTA REQUEST|REQUEST RECEIVED|MODEL LOAD|REAL INPUT|INFERENCE|postprocess|PREDICT_RAW|RESPONSE|PENDING|Traceback|Exception|Error|Timeout|Killed|MemoryError' \
"$LOG" | tail -100 | cut -c1-240

echo "=== LOG SIZE AND FINAL EVENTS ==="
wc -l "$LOG"
tail -30 "$LOG" | cut -c1-240
