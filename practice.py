python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

# Bind the two anonymous RMSNorm weights to unique CTA registry names.
s=s.replace(
'''self.norm1 = RMSNorm(256, dtype)''',
'''self.norm1 = RMSNorm(256, dtype)
        self.norm1.weight.name = "sequence_transformer.ptransformer.0.norm1.weight"'''
)

s=s.replace(
'''self.norm2 = RMSNorm(2048, dtype)''',
'''self.norm2 = RMSNorm(2048, dtype)
        self.norm2.weight.name = "sequence_transformer.ptransformer.0.norm2.weight"'''
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER RMSNORM REGISTRY MAPPED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
