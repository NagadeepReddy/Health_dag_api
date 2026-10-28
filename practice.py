cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
p=artifacts/v1.168-max/maxserve_cta_extension/cta_router.py && \
df -h /application1 && \
grep -Fq 'RequestID(request_id) if not isinstance(request_id, RequestID) else request_id' "$p" && \
cp -p "$p" "$p.bak_requestid" && \
sed -i 's/RequestID(request_id) if not isinstance(request_id, RequestID) else request_id/RequestID(str(request_id))/' "$p" && \
grep -n 'RequestID(str(request_id))' "$p"
