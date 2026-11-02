python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact")
p = root / "pipeline.py"
lines = p.read_text(errors="replace").splitlines()

print("=== MYPLAN FALLBACK AND INFERENCE BRANCH ===")
for n in range(3996, min(4100, len(lines)) + 1):
    print(f"{n}: {lines[n-1][:170]}")

print("\n=== EXTRA RECOMMENDATION SOURCES ===")
terms = (
    "Disney Bundle Basic",
    "DISNEY+",
    "Disney Bundle",
    "tierGroup",
    "CURRENT_PROPOSITION_LIST",
    "DEFAULT_PROPOSITION_LIST_BPLAN",
)

for file in sorted(root.rglob("*.py")):
    if ".ipynb_checkpoints" in str(file):
        continue
    for n, line in enumerate(file.read_text(errors="replace").splitlines(), 1):
        if any(term in line for term in terms):
            print(f"{file.relative_to(root)}:{n}: {line.strip()[:160]}")
            if n > 5000:
                break
PY
