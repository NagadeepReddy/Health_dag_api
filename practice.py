python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''WeightData(
        arr=arr,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )''',
'''WeightData(
        arr,
        dtype=DType.float32,
        shape=Shape(arr.shape),
    )'''
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER WEIGHTDATA FIXED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
