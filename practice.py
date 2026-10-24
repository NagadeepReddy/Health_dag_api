cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'from dataclasses import fields; from max.pipelines.architectures.llama3.arch import llama_arch; print("ARCHITECTURE FIELD TYPES:"); [print(f.name, "=", type(getattr(llama_arch, f.name)).__name__, repr(getattr(llama_arch, f.name))[:100]) for f in fields(llama_arch)]'
