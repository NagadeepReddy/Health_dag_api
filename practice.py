podman --root /application1/podman/storage \
--runroot /run/containers/storage \
exec -i cta-batch2-trace-8766-10g \
/opt/venv/bin/python -B - <<'PY'
from pathlib import Path
import os

print("=== ACTIVE BATCH-2 RUNTIME ===")
print("CWD:", os.getcwd())
print("PYTHONPATH:", os.getenv("PYTHONPATH"))

files = [
    Path("/batch2/real_max_batch2_backend.py"),
    Path("/batch2/cta_max/grecbase_aux_features_max.py"),
    Path("/batch2/cta_max/grecbase_fusion_batch2_draft.py"),
]

for p in files:
    print("\nFILE:", p)
    if not p.is_file():
        print("NOT FOUND")
        continue
    lines = p.read_text().splitlines()
    for n, line in enumerate(lines, 1):
        if any(k in line for k in (
            "reshape(", "input_types=", "grecbase_fusion",
            "grecbase_aux", "session.load("
        )):
            print(f"{n}: {line.strip()}")

print("\nFILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
PY
