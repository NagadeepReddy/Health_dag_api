podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i cta-clean-batch2-http-20261030 \
  /opt/venv/bin/python -B - <<'PY'
from pathlib import Path
import re

p = Path("/tmp/cta_clean_http_retry.log")
assert p.is_file(), "STOP: Log unavailable"

lines = p.read_text(errors="replace").splitlines()

print("=== WORKER FAILURE SUMMARY ===")
pattern = re.compile(
    r"(ModuleNotFoundError|ImportError|AttributeError|"
    r"RuntimeError|ValueError|TypeError|AssertionError|"
    r"FileNotFoundError|NameError|Error):"
)

matches = [(i, line) for i, line in enumerate(lines)
           if pattern.search(line)]

for i, line in matches[-8:]:
    print(f"LINE {i+1}: {line[:500]}")

print("=== LAST TRACEBACK END ===")
starts = [i for i, line in enumerate(lines)
          if line.startswith("Traceback (most recent call last):")]
if starts:
    for line in lines[starts[-1]:][-12:]:
        print(line[:350])
else:
    print("No Python traceback header found")

print("READ-ONLY CHECK COMPLETE")
PY
