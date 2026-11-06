cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")
pipeline = root / "model/artifacts/v1.472/core-artifact/bplan/pipeline.py"
samples = root / "model/artifacts/v1.472/core-artifact/bplan/test_samples"

print("=== BPLAN TEST SAMPLE DEPENDENCY ===")

if not pipeline.is_file():
    raise SystemExit("STOP: BPLAN pipeline missing")

lines = pipeline.read_text(errors="replace").splitlines()
matches = [i for i, line in enumerate(lines)
           if "test_samples" in line.lower()]

print("PIPELINE REFERENCES:", len(matches))

for i in matches:
    print(f"\n--- Line {i+1} ---")
    for j in range(max(0, i-7), min(len(lines), i+9)):
        print(f"{j+1}: {lines[j]}")

print("\n=== TEST SAMPLE FOLDER ===")
if samples.is_dir():
    files = [p for p in samples.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print("FILES:", len(files))
    print("SIZE MiB:", round(size / 1048576, 2))
    for p in files[:12]:
        print(p.relative_to(samples))
else:
    print("FOLDER NOT PRESENT")

print("\nNO FILES MODIFIED")
PY
