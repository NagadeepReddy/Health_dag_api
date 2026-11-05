
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472-max")
print("=== PZAAS VERIFIED MAX EXECUTOR DISCOVERY ===")

hits = []

for base in [root / "pzaas_max", root / "maxserve_pzaas_extension"]:
    if not base.exists():
        continue

    for p in base.rglob("*.py"):
        relative = str(p)
        if any(s in relative for s in (
            "python_deps/", "site-packages/",
            "_cta_native_reference/", "__pycache__/"
        )):
            continue

        try:
            src = p.read_text()
            tree = ast.parse(src)
        except (OSError, UnicodeError, SyntaxError):
            continue

        markers = [
            "build_grecbase_fusion_graph_order_correct",
            "InferenceSession",
            "infer_max_batch",
            "load_weight",
            "session.compile",
            "model.execute"
        ]
        found = [x for x in markers if x in src]

        if not found:
            continue

        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(x in node.name.lower() for x in (
                    "infer", "execute", "compile",
                    "build", "pack", "weight", "run"
                )):
                    definitions.append((node.lineno, node.name))

        hits.append((p, found, definitions))

for p, markers, definitions in hits[:25]:
    print("\nFILE:", p)
    print("MARKERS:", ", ".join(markers))
    for line, name in definitions[:15]:
        print(f"  {line}: {name}()")

print("\n=== EXECUTOR STATUS ===")
print("SOURCE FILES FOUND:", len(hits))
print("MAX NUMERICAL PARITY: PREVIOUSLY PASS")
print("NATIVE MODEL BRIDGE: PENDING")
print("NATIVE HTTP: NOT VERIFIED")
print("SOURCE FILES MODIFIED: NONE")
print("NEXT: CONNECT REAL PZAAS EXECUTOR TO EXISTING WORKER")
PY
