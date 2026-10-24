cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from dataclasses import fields; from max.pipelines.lib import SupportedArchitecture; print("CTA REGISTRATION FIELDS:"); print("\n".join(f.name for f in fields(SupportedArchitecture)))'
