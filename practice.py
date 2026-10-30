if ss -H -ltn '( sport = :18767 )' | grep -q .; then
  echo "STOP: Port 18767 is already in use"
else
  podman --root /application1/podman/storage --runroot /run/containers/storage exec -d 0c95d4a8f887 sh -c '
    export PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max
    export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
    export OTEL_SDK_DISABLED=true OTEL_METRICS_EXPORTER=none OTEL_TRACES_EXPORTER=none OTEL_LOGS_EXPORTER=none
    export HOME=/tmp TMPDIR=/tmp XDG_CACHE_HOME=/tmp/cta_batch2_cache HF_HOME=/tmp/cta_batch2_cache TORCH_HOME=/tmp/cta_batch2_cache CUDA_VISIBLE_DEVICES=""
    exec /opt/venv/bin/python -B -u -c "from maxserve_cta_extension.cta_queue_compat import install; assert install(); from maxserve_cta_extension.cta_native_launcher import main; main()" --port 18767 --model-path /workspace/artifacts/v1.168-max/cta_native_model --devices cpu --max-batch-size 2 > /tmp/cta_postman_native_18767.log 2>&1
  '
fi
