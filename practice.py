python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/.gitignore")

rules = [
    "# Generated model assets - do not commit",
    "*.npy",
    "*.npz",
    "*.pt",
    "*.pth",
    "*.onnx",
    "*.safetensors",
    "*.whl",
    "*.swp",
    "*.swo",
    "*.log",
    "/cta_max/*weights/",
]

existing = p.read_text() if p.exists() else ""
missing = [r for r in rules if r not in existing.splitlines()]

if missing:
    p.write_text(existing.rstrip("\n") + "\n\n" + "\n".join(missing) + "\n")

print("MAX GIT IGNORE: READY")
print("NEW RULES:", len(missing))
print("ORIGINAL DS CODE: UNCHANGED")
print("NO FILES DELETED, COMMITTED OR PUSHED")
PY
