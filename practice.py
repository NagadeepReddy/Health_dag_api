cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

r = Path("artifacts/v1.472")
g = Path("artifacts/v1.472-max/pzaas_max")

print("=== MAX GRAPH INPUT CONTRACT ===")
p = g / "grecbase_fusion_full_head_72_max.py"
lines = p.read_text().splitlines()

for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "def build_grecbase",
        "Graph(",
        "input_types=",
        "TensorType(",
        "graph.inputs",
        "graph.output",
        "ops.reshape"
    )):
        print(f"{i}: {line.strip()[:170]}")

print("\n=== ORIGINAL DS PREPROCESSING ===")
p = r / "core-artifact/pipeline.py"
tree = ast.parse(p.read_text())

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in (
        "preprocess", "inference", "loadModel"
    ):
        print(f"{node.name}: line {node.lineno}")
        if node.name == "preprocess":
            text = p.read_text().splitlines()
            for i in range(node.lineno-1, node.end_lineno):
                line = text[i]
                if "model_in" in line or "return " in line:
                    print(f"  {i+1}: {line.strip()[:150]}")

print("\n=== REAL PZAAS REQUEST SAMPLES ===")
for p in sorted((r / "samples").glob("*.json")):
    try:
        data = json.loads(p.read_text())
        print(p.name, "keys:",
              list(data)[:12] if isinstance(data, dict)
              else type(data).__name__)
    except Exception as e:
        print(p.name, type(e).__name__)

print("\nREAL INPUT DISCOVERY: COMPLETE")
print("ORIGINAL DS: NO FILES MODIFIED")
print("MAX INFERENCE / PARITY: PENDING")
PY
