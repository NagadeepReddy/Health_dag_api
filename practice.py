python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p) as f:
    s=f.read()

s=s.replace(
    "fn_attn_out_1_weight.npy",
    "fn_attn_out_weight.npy"
)

with open(p,"w") as f:
    f.write(s)

print("ATTN OUTPUT WEIGHT FILENAME FIXED")
PY

podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_max.py
