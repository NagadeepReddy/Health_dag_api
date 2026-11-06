
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import re
import shutil

repo = Path.cwd()
base = repo / "artifacts/v1.472-max"
original = repo / "artifacts/v1.472"

files = [
    original / "Model.py",
    original / "core-artifact/pipeline.py",
    original / "utils/dependency-utils/models.py",
    base / "pzaas_max/pzaas_weight_loader.py",
    base / "maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_spawn_worker.py",
    base / "maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_max_model_adapter.py",
    base / "maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
]

pattern = re.compile(
    r"torch\.load|np\.load|numpy\.load|"
    r"joblib\.load|pickle\.load|faiss\.read_index|"
    r"\.pt\b|\.npy\b|\.bin\b|\.pkl\b|"
    r"model[_-]settings|model[_-]path|"
    r"weights[_-]path|read_index|"
    r"__file__|os\.getcwd|"
    r"/application1/|/vzwhome/|"
    r"pzaas_max\.validation",
    re.IGNORECASE
)

print("=== PZAAS CLEAN RELEASE: RUNTIME DEPENDENCIES ===")

for path in files:
    print(f"\nFILE: {path.relative_to(repo)}")

    if not path.is_file():
        print("  MISSING — REVIEW REQUIRED")
        continue

    lines = path.read_text(errors="replace").splitlines()

    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if pattern.search(line)
    ]

    print("MATCHING RUNTIME REFERENCES:", len(matches))

    for number, line in matches[:35]:
        print(f"  {number}: {line[:180]}")

    if len(matches) > 35:
        print(f"  ... {len(matches)-35} additional references")

print("\n=== GRAPH NON-PYTHON RUNTIME ASSETS ===")

graph = base / "pzaas_max"

for path in sorted(graph.rglob("*")):
    if not path.is_file():
        continue

    if any(part in {
        "__pycache__", ".pytest_cache", ".git"
    } for part in path.parts):
        continue

    if path.suffix.lower() in {
        ".pt", ".pth", ".bin", ".npy", ".npz",
        ".pkl", ".pickle", ".json", ".safetensors"
    }:
        print(
            path.relative_to(repo),
            f"{path.stat().st_size / 1048576:.2f} MiB"
        )

print("\n=== RUNTIME VALIDATION IMPORT ===")

required = (
    graph / "validation/pzaas_forward_input_adapter.py"
)

print("FORWARD INPUT ADAPTER EXISTS:", required.is_file())

print("\n=== DEPLOYMENT CONFIGURATION ===")

for name in ("model-settings.json", "requirements.txt"):
    for path in sorted(original.rglob(name))[:10]:
        print(path.relative_to(repo))

print("\n=== AVAILABLE STAGING SPACE ===")

disk = shutil.disk_usage("/application1")
print(f"FREE: {disk.free / 1073741824:.1f} GiB")

print("\n=== NEXT ACTION ===")
print("Construct minimal PZAAS runtime manifest")
print("Separate reusable MAX runtime from model files")
print("Stage a clean release without changing existing POC")
print("NO FILES MODIFIED OR DELETED")
PY
