python3 - <<'PY'
from pathlib import Path
import ast

base = Path("/application1")
dev = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
backend = dev / "real_max_batch2_backend.py"
contract = (
    base / "cta_max_true_batch_dev_20261028"
    / "batch2_candidate/cta_max/run_batch2_contract.py"
)

assert backend.is_file(), "STOP: Backend missing"
assert contract.is_file(), "STOP: Contract missing"

for name, path in [
    ("BACKEND", backend),
    ("CONTRACT", contract),
]:
    source = path.read_text()
    tree = ast.parse(source)

    print(f"\n=== {name} ===")
    print("SYNTAX: PASS")

    for number, line in enumerate(source.splitlines(), 1):
        if (
            number <= 45
            or "batch2_contract" in line
            or "pack_two_requests" in line
        ):
            print(f"{number:4}: {line}")

    if name == "CONTRACT":
        print(
            "PACKER DEFINED:",
            any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "pack_two_requests"
                for node in ast.walk(tree)
            )
        )

print("\nREAD-ONLY INSPECTION COMPLETE")
print("NO FILES MODIFIED")
PY
