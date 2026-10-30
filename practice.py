python3 - <<'PY'
from pathlib import Path

base = Path("/application1")
files = [
    base / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/parallel_transformer_block_2layers.py",
    base / "CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py",
    base / "CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_after_cache_fix.log",
]

for p in files:
    print(f"\n===== {p.name} =====")
    if not p.is_file():
        print("FILE NOT FOUND")
        continue

    lines = p.read_text(errors="replace").splitlines()

    if p.suffix == ".log":
        selected = [
            (i, line) for i, line in enumerate(lines, 1)
            if any(k in line.lower() for k in
                   ("pass", "weight", "batch", "error"))
        ]
        for i, line in selected[-25:]:
            print(f"{i}: {line[:250]}")
    else:
        for i, line in enumerate(lines, 1):
            if any(k in line.lower() for k in
                   ("weight", "np.load", "sequence_weights",
                    "model.execute", "sys.path", "chdir")):
                start = max(0, i - 3)
                end = min(len(lines), i + 3)
                print(f"\nLINES {start+1}-{end}")
                for j in range(start, end):
                    print(f"{j+1}: {lines[j]}")

print("\nREAD-ONLY INSPECTION COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
