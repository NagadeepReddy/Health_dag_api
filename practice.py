cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -n -C 6 -E \
'CTA HTTP QUEUE ITEM|_cta_http_loop|call_soon_threadsafe|pending\[rid\]|response_queue.get' \
artifacts/v1.168-max/maxserve_cta_extension/{cta_router.py,cta_native_live_server.py}
