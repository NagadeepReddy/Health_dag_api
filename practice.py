python - <<'PY'
import ast
import json
from pathlib import Path

root = Path("artifacts/v1.168")
source = (root / "utils/dependency-utils/models.py").read_text()
tree = ast.parse(source)

cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)

init = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "__init__"
)

print("===== NLP CONSTRUCTOR PARAMETERS =====")
for arg in init.args.args:
    if "nlp" in arg.arg.lower():
        print(arg.arg)

print("\n===== NLP CONFIGURATION FILES =====")
configs = sorted(root.rglob("config.json"))

for p in configs:
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        continue

    if not isinstance(data, dict):
        continue

    if any(k in data for k in (
        "model_type", "hidden_size", "num_hidden_layers"
    )):
        print("PATH:", p)
        for key in (
            "model_type",
            "architectures",
            "hidden_size",
            "num_hidden_layers",
            "num_attention_heads",
            "intermediate_size",
            "max_position_embeddings"
        ):
            if key in data:
                print(f"  {key}: {data[key]}")

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
