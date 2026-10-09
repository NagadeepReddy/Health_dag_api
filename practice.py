podman run --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
sys.path.insert(0, "/workspace")

p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

# Execute only the runner setup before the failing mapping/session.load.
src=open(p).read()
cut=src.find('# RMSNorm internally requests')
if cut < 0:
    cut=src.find('model = session.load')

assert cut >= 0, "Could not locate registry/load section"

exec(src[:cut], globals())

print("\n=== ACTUAL WEIGHTS REGISTRY KEYS ===")
for k in sorted(weights.keys()):
    print(k)

print("\n=== NORM KEYS ===")
for k in sorted(weights.keys()):
    if "norm" in k.lower():
        print(k)

print("\nREGISTRY INSPECTION COMPLETE")
PY
