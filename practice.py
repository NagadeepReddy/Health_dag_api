BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts
echo "=== ORIGINAL CTA FOLDERS ==="
du -sh "$BASE/v1.168"/{config,core-artifact,lookup,utils,samples} 2>/dev/null
echo "=== MAX FOLDERS ==="
du -sh "$BASE/v1.168-max"/{cta_native_model,cta_native_batch2_release_candidate} 2>/dev/null
echo "=== AVAILABLE DISK ==="
df -h /application1
