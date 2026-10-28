echo "=== NATIVE RESPONSE RECEIVER DIAGNOSTICS ==="
grep -nEi \
'CTA RECEIVER|CTA QUEUE INITIALIZED|CTA ZMQ|response.worker|response.queue|worker.health|Traceback|Exception|KeyError|RuntimeError' \
/application1/cta_native_corrected_1028.log \
| tail -65
