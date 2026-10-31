python3 -B - <<'PY'
from pathlib import Path

roots = {
    "CLEAN": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max"),
    "ORIGINAL": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max"),
    "DEVELOPMENT": Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate"),
}

for label, root in roots.items():
    print(f"\n=== {label} ===")
    for name in ("nlp_bert_max.py", "__init__.py"):
        matches = list(root.glob(f"cta_max/{name}"))
        print(name, "FOUND" if matches else "MISSING")
        for p in matches:
            print(p)

print("\nREAD-ONLY CHECK COMPLETE")
PY
