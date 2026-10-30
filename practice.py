podman --root /application1/podman/storage \
--runroot /run/containers/storage \
exec -i cta-batch2-trace-8766-10g \
/opt/venv/bin/python -B - <<'PY'
import importlib.util
from pathlib import Path

print("=== REAL BATCH-2 IMPORT CHECK ===")

spec = importlib.util.find_spec("cta_max")
print("ACTIVE CTA PACKAGE:", list(spec.submodule_search_locations) if spec and spec.submodule_search_locations else "NOT FOUND")

roots = [
    Path("/batch2/cta_max"),
    Path("/workspace/artifacts/v1.168-max/cta_max"),
]

for root in roots:
    for name in (
        "grecbase_aux_branches_max.py",
        "grecbase_aux_features_max.py",
        "grecbase_fusion_batch2_draft.py",
    ):
        p = root / name
        if not p.is_file():
            continue

        print("\nFILE:", p)
        lines = p.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            if any(x in line for x in (
                "def grecbase_aux_features",
                "from cta_max.grecbase_aux",
                "ops.reshape(",
                "grecbase_aux_features("
            )):
                print(f"{i}: {line.strip()}")

print("\nFILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
PY
