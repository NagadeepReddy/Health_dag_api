podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /opt/venv/bin/python -B - <<'PY'
from pathlib import Path

p = Path("/tmp/cta_clean_http.log")
assert p.is_file(), "STOP: Startup log missing"

lines = p.read_text(errors="replace").splitlines()
print("=== WORKER ERROR DETAILS ===")

markers = (
    "Traceback", "Error:", "Exception:",
    "ModuleNotFoundError", "ImportError",
    "RuntimeError", "TimeoutError"
)
matches = [i for i, line in enumerate(lines)
           if any(x in line for x in markers)]

for i in matches[-8:]:
    print(f"\n--- Log line {i+1} ---")
    for line in lines[max(0, i-3):min(len(lines), i+5)]:
        print(line[:250])

print("\n=== LAST 12 LOG LINES ===")
for line in lines[-12:]:
    print(line[:250])

print("READ-ONLY CHECK COMPLETE")
PY
