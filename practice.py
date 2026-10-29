echo "=== LIVE MAX TEST ==="
tail -n 45 /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_http_batch2_healthfix_retry.log

echo "=== PROCESS STATUS ==="
ps -eo pid,etime,stat,args | grep -E 'native_http_batch2_healthfix_runner|timeout -k 15s 330s|podman.*cta-max-faiss' | grep -v grep || true
