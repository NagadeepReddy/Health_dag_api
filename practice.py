
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

root = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension"
)

worker = root / "pzaas_native_serve_dev/pzaas_worker_adapter.py"

print("=== WORKER INITIALIZATION ===")

if not worker.is_file():
    raise SystemExit("STOP: Worker adapter missing")

lines = worker.read_text().splitlines()

for i in range(min(24, len(lines))):
    print(f"{i+1}: {lines[i]}")

print("\n=== PIPELINE FACTORY AND MAX HOOK WIRING ===")

terms = (
    "pipeline_factory",
    "attach_max",
    "PZAASWorkerAdapter(",
    "PZAASNativeWorkerAdapter(",
    "pipeline.load(",
    "def create_pipeline",
    "def build_pipeline",
    "def make_pipeline",
)

shown = 0

for file in sorted(root.rglob("*.py")):
    if file == worker:
        continue

    content = file.read_text(errors="replace").splitlines()

    matches = [
        i for i, line in enumerate(content)
        if any(term in line for term in terms)
    ]

    if not matches:
        continue

    print(f"\nFILE: {file}")

    indices = set()
    for i in matches:
        indices.update(
            range(max(0, i-3), min(len(content), i+5))
        )

    for i in sorted(indices):
        print(f"{i+1}: {content[i]}")
        shown += 1
        if shown >= 130:
            break

    if shown >= 130:
        print("OUTPUT LIMIT REACHED")
        break

print("\n=== INSPECTION COMPLETE: NO FILES MODIFIED ===")
PY
