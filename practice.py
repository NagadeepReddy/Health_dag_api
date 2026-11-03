cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.472/core-artifact/pipeline.py")
s = p.read_text().splitlines()

print("=== INFERENCE BRANCHES AND MODEL CALLS ===")
for i in range(4716, min(5013, len(s))):
    line = s[i].strip()
    if (line.startswith(("if ", "elif ", "else:", "return "))
        or "self.model_" in line
        or "enable_model" in line):
        print(f"{i+1}: {line[:170]}")

print("\n=== AVAILABLE TEST FIXTURES ===")
root = Path("artifacts/v1.472")
paths = sorted(
    p for p in root.rglob("*.json")
    if any(x in str(p).lower() for x in ("sample", "sanity", "test_input"))
)
for p in paths[:15]:
    print(p)
print("Total matching fixtures:", len(paths))
PY
