python3 - <<'PY'
from pathlib import Path
import hashlib
import difflib

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max")
name = "grecbase_fusion_full_head_72_max.py"

original = root / "maxserve_bplan_extension/bplan_max_dev" / name
staged = root / "bplan_batch2_graph_dev" / name

for p in (original, staged):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing {p}")

a = original.read_bytes()
b = staged.read_bytes()

print("ORIGINAL SHA256:", hashlib.sha256(a).hexdigest())
print("ISOLATED SHA256:", hashlib.sha256(b).hexdigest())
print("FILES IDENTICAL:", a == b)

if a != b:
    print("\n=== EXISTING DIFFERENCES ===")
    changes = list(difflib.unified_diff(
        original.read_text().splitlines(),
        staged.read_text().splitlines(),
        fromfile="original",
        tofile="isolated",
        lineterm=""
    ))
    print("\n".join(changes[:100]))

print("\n=== ISOLATED GRAPH SOURCE ===")
for n, line in enumerate(staged.read_text().splitlines(), 1):
    print(f"{n:3}: {line}")

print("\nREAD-ONLY VERIFICATION COMPLETE")
PY
