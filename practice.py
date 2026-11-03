cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json, sys

r = Path("artifacts/v1.472")
p = r/"core-artifact/model_0_base.pt"
cfg = json.loads((r/"config/torch_model_params_base.json").read_text())
if isinstance(cfg, list):
    cfg = cfg[0]

print("=== PZAAS BASE CONFIG ===")
for k in ("deep_dims", "seq_dim", "task_out_dims",
          "sibling_deep_dims", "nlp_embed_dim"):
    print(k, "=", cfg.get(k))

print("\n=== CHECKPOINT ===")
if not p.is_file():
    sys.exit("CHECKPOINT MISSING")

size = p.stat().st_size
print("Size GiB:", round(size / 2**30, 2))

mem = 0
for line in Path("/proc/meminfo").read_text().splitlines():
    if line.startswith("MemAvailable:"):
        mem = int(line.split()[1]) * 1024

if mem < max(18 * 2**30, size * 4):
    sys.exit("RAM GUARD: SKIPPED CHECKPOINT LOAD")

try:
    import torch
except ImportError:
    sys.exit("PyTorch unavailable on host; inspect in approved container next")

try:
    state = torch.load(p, map_location="cpu", weights_only=True)
except Exception as e:
    sys.exit(f"SAFE LOAD UNAVAILABLE: {type(e).__name__}: {str(e)[:150]}")

if isinstance(state, dict) and isinstance(state.get("state_dict"), dict):
    state = state["state_dict"]

if not isinstance(state, dict):
    sys.exit("Unexpected checkpoint format")

tensors = [(k, tuple(v.shape)) for k,v in state.items()
           if hasattr(v, "shape")]
print("Total tensors:", len(tensors))
print("\n=== KEY WEIGHT SHAPES ===")
hits = [(k,v) for k,v in tensors if any(x in k.lower()
        for x in ("seq", "dense", "nlp", "sibling", "task"))]
for k,v in hits[:45]:
    print(k, v)
print("Matching tensors:", len(hits))
print("\nPZAAS WEIGHT SHAPE INSPECTION: COMPLETE")
PY
