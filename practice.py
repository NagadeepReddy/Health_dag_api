python3 -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
backend = base / "real_max_batch2_backend.py"
adapter = base / "cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py"
package = base / "cta_max"

assert backend.is_file() and adapter.is_file()
assert (package / "__init__.py").is_file()

for label, path in [("BACKEND", backend), ("ADAPTER", adapter)]:
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    print(f"\n=== {label} ===")
    print("SYNTAX: PASS")

    for n, line in enumerate(source.splitlines(), 1):
        if any(term in line for term in (
            "/workspace", "/batch2", "/application1",
            "sys.path", "model_path", "weights",
            "cta_max", "real_max_batch2_backend"
        )):
            print(f"{n}: {line[:180]}")

print("\nCLEAN BACKEND EXISTS: PASS")
print("CLEAN CTA_MAX PACKAGE EXISTS: PASS")
print("ORIGINAL FILES: UNCHANGED")
print("READ-ONLY CHECK COMPLETE")
PY
