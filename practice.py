cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import multiprocessing as mp; from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper; p=mp.get_context("spawn").Process(target=CTAFactoryWrapper(dict)); p.start(); p.join(30); print("CTA CHILD PROCESS:", "PASS" if p.exitcode==0 else f"FAIL exit={p.exitcode}", flush=True); p.terminate() if p.is_alive() else None'
