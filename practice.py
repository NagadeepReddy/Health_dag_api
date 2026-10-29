python3 -S -B - <<'PY'
from pathlib import Path

log = Path("/application1/cta_concurrency_retest_20261029.log")
src = Path("/application1/cta_max_native_release_candidate_20261028/cta_http_pipeline.py")

assert log.is_file() and src.is_file(), "STOP: Required file missing"

lines = log.read_text(errors="replace").splitlines()

print("=== RESPONSE RECEIVER ERRORS / LIFECYCLE ===")
terms = (
    "RESPONSE WORKER LOOP",
    "HTTP RESPONSE DELIVERED",
    "RESPONSE QUEUE SEND",
    "response_worker",
    "CancelledError",
    "zmq.Again",
    "queue.Empty",
    "Socket is closed",
    "Worker failed",
    "Task exception",
    "Traceback",
)

for i, line in enumerate(lines, 1):
    if any(t.lower() in line.lower() for t in terms):
        print(f"{i}: {line[:300]}")

print("\n=== PATCHED RECEIVER IMPLEMENTATION ===")
source = src.read_text().splitlines()
for i, line in enumerate(source, 1):
    if (
        "def _cta_fast_response_worker" in line
        or "def _cta_safe_get_nowait" in line
    ):
        for j in range(i, min(i + 35, len(source) + 1)):
            print(f"{j}: {source[j-1]}")
        print("---")

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
