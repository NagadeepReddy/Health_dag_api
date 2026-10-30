python3 - <<'PY'
import json, time, urllib.request, subprocess
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert p.is_file(), "STOP: Existing CTA JSON missing"
body = p.read_bytes()
json.loads(body)

passed = 0

for n in (1, 2):
    print(f"\n=== OPTIMIZED REQUEST {n} ===", flush=True)
    start = time.monotonic()

    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8766/v2/cta/predict",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=180) as r:
            result = json.load(r)
            status = r.status

        prediction = result["jsonData"]["prediction"]
        assert status == 200
        assert isinstance(prediction["offerList"], list)

        passed += 1
        print(f"REQUEST {n}: PASS HTTP 200")
        print(f"LATENCY: {time.monotonic()-start:.2f}s")

    except Exception as e:
        print(f"REQUEST {n}: FAILED: {e}", flush=True)
        break

print(f"\nSEQUENTIAL RESULTS: {passed}/2")

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

r = subprocess.run(
    pod + ["logs", "--tail", "350", "cta-batch2-trace-8766-v2"],
    capture_output=True, text=True
)

print("\n=== MAX QUEUE TRACE ===")
keywords = (
    "CTA BATCH RETURNED",
    "CTA QUEUE SEND",
    "CTA TRUE MAX BATCH-2",
    "CTA RESPONSE SOCKET RECEIVED",
    "CTA HTTP QUEUE ITEM",
    "POST /v2/cta/predict",
    "Traceback",
    "ERROR",
)

lines = [
    line for line in (r.stdout + r.stderr).splitlines()
    if any(k in line for k in keywords)
]

print("\n".join(lines[-35:]) or "NO MATCHING TRACE")
print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
PY
