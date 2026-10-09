python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
    "ops.softmax(scores, axis=-1)",
    "ops.softmax(scores, -1)"
)

with open(p,"w") as f:
    f.write(s)

print("MAX SOFTMAX AXIS FIXED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
