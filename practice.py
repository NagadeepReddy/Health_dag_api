python3 - <<'PY'
from pathlib import Path
import subprocess

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
original = p.read_bytes()
fixed = original.rstrip(b"\r\n") + b"\n"

if original != fixed:
    p.write_bytes(fixed)
    print("EXTRA BLANK LINE REMOVED")

subprocess.run(["git", "add", "--", str(p)], check=True)
subprocess.run(["git", "diff", "--cached", "--check"], check=True)

result = subprocess.check_output(
    ["git", "diff", "--cached", "--name-only"], text=True
)
print("GIT FORMATTING CHECK: PASS")
print("STAGED FILES:", len(result.splitlines()))
print("NOT COMMITTED OR PUSHED")
PY
