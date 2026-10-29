podman --root /application1/podman/storage --runroot /run/containers/storage run --rm \
  --network=none --read-only \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /root:rw,size=64m \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -v /application1/CTA_MAX_TRUE_BATCH2_DEV_20261029:/batch2:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  /batch2/run_real_sanity_input_adapter.py
