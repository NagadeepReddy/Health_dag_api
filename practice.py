podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from max.pipelines.architectures.llama3.arch import llama_arch

for name in ("default_encoding", "default_weights_format"):
    value = getattr(llama_arch, name)
    enum_type = type(value)
    print(name, "=", value)
    print("VALID OPTIONS:", [x.name for x in enum_type])
'
