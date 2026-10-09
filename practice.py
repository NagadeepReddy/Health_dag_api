python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
    'RMSNorm(256, dtype, name="sequence_transformer.ptransformer.0.norm1")',
    'RMSNorm(256, dtype)'
)

s=s.replace(
    'RMSNorm(2048, dtype, name="sequence_transformer.ptransformer.0.norm2")',
    'RMSNorm(2048, dtype)'
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER RMSNORM NAME FIXED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
