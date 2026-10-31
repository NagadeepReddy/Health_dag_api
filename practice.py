python3 -B - <<'PY'
from pathlib import Path

base = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max")
p = base / "real_max_batch2_backend.py"

assert p.is_file(), "STOP: clean backend missing"

text = p.read_text()
terms = [
    "cta_max_true_batch_dev_20261028",
    "/batch2/cta_max",
    "run_batch2_contract",
    "from pathlib import Path",
]

for term in terms:
    print(f"\n=== {term} | OCCURRENCES: {text.count(term)} ===")
    for n, line in enumerate(text.splitlines(), 1):
        if term in line:
            print(f"{n}: {line.strip()!r}")

print("\nORIGINAL FILES: UNCHANGED")
print("READ-ONLY CHECK COMPLETE")
PY
