cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

REPO="$PWD"
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CANDIDATE=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
RUNNER="$DEV/run_distinct_batch2_live_max_inference.py"
SECOND="$DEV/second_real_cta_model_in.pt"

test -s "$RUNNER" || { echo "STOP: Runner missing"; exit 1; }
test -s "$SECOND" || { echo "STOP: Second captured input missing"; exit 1; }
test -s "$REPO/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt" || {
  echo "STOP: First saved input missing"
  exit 1
}

echo "=== EXECUTING TWO DISTINCT REAL CTA INPUTS ==="

timeout 300s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 6g --cpus 2 --pids-limit 128 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e CTA_SECOND_MODEL_INPUT=/batch2/second_real_cta_model_in.pt \
  -e PYTHONPATH="$CANDIDATE:/workspace/artifacts/v1.168-max" \
  -v "$REPO:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CANDIDATE:$CANDIDATE:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -B /batch2/run_distinct_batch2_live_max_inference.py

echo "DISTINCT-INPUT RUNNER: COMPLETED"
echo "ORIGINAL DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
