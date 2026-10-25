podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from dataclasses import fields
from max.pipelines.architectures.llama3.arch import llama_arch

for f in fields(llama_arch):
    if any(x in f.name.lower() for x in
           ("weight", "encoding", "model", "task", "pipeline", "quant")):
        print(f.name, "=", str(getattr(llama_arch, f.name))[:300])
'
