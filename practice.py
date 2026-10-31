BASE=/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== NATIVE WORKER SPAWN IMPLEMENTATION ==="
sed -n '1,115p' "$BASE/cta_spawn_worker.py"
