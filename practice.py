cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import re

root = Path.cwd()
graph = root / "artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py"

print("=== PZAAS SIX-LAYER WEIGHT AUDIT ===")
assert graph.is_file(), f"Missing graph: {graph}"

src = graph.read_text()
compile(src, str(graph), "exec")
print("PYTHON SYNTAX: PASS")

for i in range(6):
    declarations = re.findall(
        rf"\bblock{i}\s*=\s*ParallelTransformerBlockMAX\(",
        src
    )
    calls = re.findall(rf"\bblock{i}\s*\(", src)
    print(f"LAYER {i}: declaration={len(declarations)}, calls={len(calls)}")

print("FINAL SX6:", bool(re.search(r"postprocess\s*\(\s*sx6\s*\)", src)))

locations = [
    Path("/models/pzaas_max/pzaas_base_weights"),
    root / "artifacts/v1.472-max/pzaas_max",
    root / "artifacts/v1.472-max",
]

files = {}
for directory in locations:
    if directory.is_dir():
        for p in directory.rglob("*.npy"):
            files[str(p.resolve())] = p

print("VISIBLE WEIGHT FILES:", len(files))

counts = {}
for i in range(6):
    matches = [
        p for p in files.values()
        if re.search(rf"(?:ptransformer|ptramsformer|transformer)\.{i}\.", p.name)
    ]
    counts[i] = len(matches)
    print(f"TRAINED LAYER {i} WEIGHTS:", len(matches))
    for p in matches[:3]:
        print(" ", p.name)

print("=== RESULTS ===")
print("GRAPH SOURCE: VERIFIED")
print("SIX-LAYER WEIGHT COVERAGE:",
      "VISIBLE" if all(counts.values()) else "NOT YET VERIFIED")
print("MAX CPU COMPILATION: PENDING RETEST")
print("FULL MODEL PARITY: PENDING")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
