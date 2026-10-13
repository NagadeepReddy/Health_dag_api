cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

RUNNER=artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py

if grep -q 'grecbase_fusion_order_correct_max' "$RUNNER"; then
  podman run --rm -i \
    -v "$PWD:/workspace" \
    -w /workspace \
    --entrypoint python \
    docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
    "$RUNNER"
else
  echo "STOP: Runner does not directly reference the corrected graph."
  grep -nE '^from |^import |grecbase_fusion|build_' "$RUNNER"
fi
