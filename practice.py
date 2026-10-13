python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
lines = p.read_text().splitlines()

print("=== ORIGINAL MODEL LOADING AND EXECUTION ===")
terms = (
    "GRecBase(",
    "loadBaseModel(",
    "load_state_dict(",
    "model.eval(",
    "self.model(",
    "model_in",
)

seen = set()
for i, line in enumerate(lines):
    if any(t in line for t in terms):
        lo, hi = max(0, i-5), min(len(lines), i+9)
        for j in range(lo, hi):
            if j not in seen:
                print(f"{j+1}: {lines[j]}")
                seen.add(j)
        print("---")

print("READ ONLY — NO FILES MODIFIED")
PY
