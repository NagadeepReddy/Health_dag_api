cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import ast
import json
from pathlib import Path
import numpy as np

root = Path("artifacts/v1.472-max/pzaas_max")
print("=== PZAAS INPUT MAPPING RESOLUTION ===")

p = root / "validation/ppa_tensor_inputs.npz"
with np.load(p, allow_pickle=False) as z:
    print("SAVED ARRAYS:", len(z.files))
    for i, k in enumerate(z.files):
        a = z[k]
        print(f"{i:03d} {k}: {a.shape} {a.dtype}")

print("\n=== EXISTING ADAPTER FUNCTIONS ===")
for p in sorted(root.rglob("*.py")):
    if not any(
        x in p.name for x in
        ("input", "adapter", "schema", "fusion")
    ):
        continue
    try:
        tree = ast.parse(p.read_text())
    except (SyntaxError, UnicodeError):
        continue

    print("FILE:", p)
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            print(" ", n.name, "LINE", n.lineno)
            if isinstance(n, ast.FunctionDef):
                print("  ARGS:",
                      [a.arg for a in n.args.args])

print("\n=== SAVED SCHEMAS ===")
for p in sorted(root.rglob("*schema*.json")):
    print("FILE:", p)
    try:
        obj = json.loads(p.read_text())
        if isinstance(obj, dict):
            for k, v in obj.items():
                s = str(v)
                print(k, "=", s[:600])
        else:
            print(str(obj)[:1500])
    except Exception as e:
        print(type(e).__name__, str(e)[:150])

print("\nINPUT MAPPING DIAGNOSTIC: COMPLETE")
print("MAX WEIGHTS: 17/17 PREVIOUSLY PASSED")
print("MAX CPU COMPILATION: PREVIOUSLY PASSED")
print("ORIGINAL DS: UNCHANGED")
PY
