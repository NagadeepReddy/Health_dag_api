python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
ext = root / "artifacts/v1.113-max/maxserve_bplan_extension"

for p in sorted(ext.rglob("*.py")):
    if not any(x in p.name for x in ("registration", "factory", "hook")):
        continue
    lines = p.read_text(errors="replace").splitlines()
    hits = [i for i, s in enumerate(lines)
            if any(x in s.lower() for x in (
                "pipeline_factory", "bplanmaxmodel",
                "pipeline(", "predict_raw", "max_factory"
            ))]
    if hits:
        print(f"\n=== {p.relative_to(ext)} ===")
        shown = set()
        for i in hits:
            for j in range(max(0,i-4), min(len(lines),i+7)):
                if j not in shown:
                    print(f"{j+1}: {lines[j]}")
                    shown.add(j)

print("\n=== BPLAN TEST SAMPLES ===")
samples = root / "artifacts/v1.113/core-artifact/test_samples"
for p in sorted(samples.glob("*.json"))[:10]:
    print(p.name)
PY
