cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import pickle; from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper; f=CTAFactoryWrapper(dict); restored=pickle.loads(pickle.dumps(f)); p=restored(); print("FACTORY SERIALIZATION: PASS"); print("CTA ADAPTER:", hasattr(p,"cta_adapter")); print("NATIVE FLAG:", getattr(p,"_cta_native_pipeline",False))'
