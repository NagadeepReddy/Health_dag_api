
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json
import os

base = Path("artifacts/v1.472")
pipeline = base / "core-artifact/pipeline.py"

print("=== PZAAS ORIGINAL DEBERT CONFIG RESOLUTION ===")

print("\n=== ORIGINAL PIPELINE PATHS ===")
if pipeline.is_file():
    lines = pipeline.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        if any(x in line.lower() for x in (
            "dbert_path",
            "nlp_encoder_path",
            "deberta"
        )):
            print(f"{i}: {line.strip()}")

print("\n=== ORIGINAL MODEL PARAMETERS ===")
for p in sorted(base.rglob("torch_model_params_base.json")):
    data = json.loads(p.read_text())
    data = data[0] if isinstance(data, list) else data
    print("PARAMETER FILE:", p)
    for key in (
        "nlp_encoder_path",
        "nlp_embed_dim",
        "sequence_transformer_kwargs"
    ):
        print(key, "=", data.get(key))

print("\n=== EXISTING DEBERT CONFIG CANDIDATES ===")
found = []

for root, dirs, files in os.walk("/application1"):
    dirs[:] = [
        d for d in dirs
        if d not in (
            "podman", ".git", "__pycache__",
            "node_modules"
        )
    ]

    if "config.json" not in files:
        continue

    p = Path(root) / "config.json"

    try:
        obj = json.loads(p.read_text())
        model_type = str(obj.get("model_type", "")).lower()
        architectures = str(obj.get("architectures", "")).lower()

        if "debert" in model_type or "debert" in architectures:
            found.append(p)
            print("FOUND:", p)
            print("MODEL TYPE:", model_type)
            print("HIDDEN SIZE:", obj.get("hidden_size"))
            print("LAYERS:", obj.get("num_hidden_layers"))
    except (OSError, ValueError):
        continue

print("\n=== RESULTS ===")
print("DEBERT CANDIDATES:", len(found))
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
print(
    "NEXT:",
    "MATCH CONFIG WITH ORIGINAL PIPELINE"
    if found else
    "LOCATE ORIGINAL EXTERNAL DEBERT MODEL ASSET"
)
PY
