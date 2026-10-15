python3 - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.168-max")
runtime = {
    Path(line.strip()).name
    for line in (root / "RELEASE_CANDIDATE.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
}

files = sorted((root / "cta_max").glob("*.py"))
remaining = [p for p in files if p.name not in runtime]

keywords = (
    "diag", "trial", "test", "parity",
    "before", "backup", "debug", "compare",
    "validate", "check"
)

experimental = [p for p in remaining if any(k in p.name.lower() for k in keywords)]
review = [p for p in remaining if p not in experimental]

print("REQUIRED RUNTIME:", len(runtime))
print("POSSIBLE DIAGNOSTICS:", len(experimental))
print("OTHER FILES TO REVIEW:", len(review))

print("\nOTHER FILES TO REVIEW:")
for p in review:
    print(" ", p.name)

print("\nNO FILES MOVED OR DELETED")
PY
