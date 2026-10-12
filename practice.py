python - <<'PY'
from pathlib import Path
import importlib.util
import subprocess

root = Path("artifacts/v1.168")

print("=== HOST FAISS ===")
print("Available:", importlib.util.find_spec("faiss") is not None)

print("\n=== ORIGINAL DEPENDENCY DECLARATIONS ===")
files = [
    p for p in root.rglob("*")
    if p.is_file() and (
        p.name.startswith("requirements")
        or p.name in ("Dockerfile", "environment.yml", "pyproject.toml")
    )
]

for p in files[:12]:
    print("FILE:", p)
    lines = p.read_text(errors="replace").splitlines()
    matches = [
        (i, line) for i, line in enumerate(lines, 1)
        if any(x in line.lower() for x in (
            "faiss", "torch", "transformers", "python", "from "
        ))
    ]
    for i, line in matches[:8]:
        print(f"  {i}: {line[:140]}")

print("\n=== AVAILABLE CONTAINER IMAGES ===")
r = subprocess.run(
    ["podman", "images", "--format", "{{.Repository}}:{{.Tag}}"],
    capture_output=True, text=True
)
if r.returncode == 0:
    for line in r.stdout.splitlines()[:20]:
        print(line)
else:
    print(r.stderr[:300])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
