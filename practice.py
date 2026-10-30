run_cta_batch2() {
  local R=/application1
  local DEV=$R/CTA_MAX_TRUE_BATCH2_DEV_20261029
  local CAND=$R/cta_max_true_batch_dev_20261028/batch2_candidate
  local REPO=$R/sajjna8/rt-pzaas-cta-offers-v1
  local NAME=cta-batch2-importfirst-8766
  local POD=(podman --root "$R/podman/storage" --runroot /run/containers/storage)

  test -f "$DEV/native_batch2_cached_overlay/cta_native_batch2_import_first.py" || {
    echo "STOP: Launcher missing"; return 1;
  }
  test -f "$CAND/cta_max/grecbase_aux_features_max.py" || {
    echo "STOP: Batch-2 candidate missing"; return 1;
  }
  test -f "$DEV/real_max_batch2_backend.py" || {
    echo "STOP: Real MAX backend missing"; return 1;
  }
  test -d "$DEV/mojo_cache_8766" || {
    echo "STOP: Existing Mojo cache missing"; return 1;
  }
  if "${POD[@]}" container exists "$NAME"; then
    echo "STOP: Container name already exists"
    return 1
  fi
  python3 -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0",8766)); s.close()' || {
    echo "STOP: Port 8766 occupied"; return 1;
  }

  "${POD[@]}" run -d \
    --name "$NAME" \
    --network host \
    --read-only \
    --memory 1700m \
    --memory-swap 1700m \
    --tmpfs /tmp:rw,exec,size=1024m \
    --tmpfs /run:rw,size=64m \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e PYTHONPATH=/batch2:/workspace:/workspace/artifacts/v1.168-max \
    -v "$REPO:/workspace:ro" \
    -v "$DEV/native_batch2_cached_overlay:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -v "$CAND:/batch2:ro" \
    -v "$DEV/real_max_batch2_backend.py:/batch2/real_max_batch2_backend.py:ro" \
    -v "$DEV/mojo_cache_8766:/opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw" \
    -w /workspace \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_import_first.py
}

run_cta_batch2
