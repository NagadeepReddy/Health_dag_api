cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import pickle; from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper; from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook; print("CTA WORKER MODULES: PASS"); print("FACTORY PICKLE:", end=" "); f=CT AFactoryWrapper(lambda: None); print("PASS" if pickle.dumps(f) else "FAIL")'
