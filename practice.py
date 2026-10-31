PODMAN="podman --root /application1/podman/storage --runroot /run/containers/storage"
NAME="cta-clean-batch2-http-20261030"

AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAILABLE" -ge 18874368 || { echo "STOP: Insufficient RAM"; exit 1; }

STATE=$($PODMAN inspect "$NAME" --format '{{.State.Status}}') || exit 1
test "$STATE" = "running" || { echo "STOP: Clean container is not running"; exit 1; }

$PODMAN exec -d \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e CUDA_VISIBLE_DEVICES= \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp/cta_batch2_cache \
  -e HF_HOME=/tmp/cta_batch2_cache \
  -e TORCH_HOME=/tmp/cta_batch2_cache \
  -e OTEL_SDK_DISABLED=true \
  -e OTEL_METRICS_EXPORTER=none \
  -e OTEL_TRACES_EXPORTER=none \
  -e OTEL_LOGS_EXPORTER=none \
  "$NAME" \
  /bin/sh -c 'timeout -s TERM -k 10s 360s /opt/venv/bin/python -B -u -c "from maxserve_cta_extension.cta_queue_compat import install; assert install(); from maxserve_cta_extension.cta_native_launcher import main; main()" --port 18767 --model-path /workspace/artifacts/v1.168-max/cta_native_model --devices cpu --max-batch-size 2 > /tmp/cta_clean_http.log 2>&1'
