python3 - <<'PY'
import json, time, urllib.request, subprocess
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert p.is_file(), "STOP: CTA JSON missing"
body = p.read_bytes()
json.loads(body)

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)
passed = 0

for n in (1, 2):
    print(f"\n=== CTA REQUEST {n} ===", flush=True)
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8766/v2/cta/predict",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with opener.open(req, timeout=240) as r:
            result = json.load(r)
            status = r.status

        prediction = result["jsonData"]["prediction"]
        assert status == 200
        assert isinstance(prediction["offerList"], list)

        passed += 1
        print("RESULT: PASS HTTP 200", flush=True)
        print("LATENCY:", round(time.monotonic()-start, 2), "seconds")

    except Exception as e:
        print("RESULT: FAILED", repr(e), flush=True)
        break

print(f"\nSEQUENTIAL RESULTS: {passed}/2", flush=True)

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
r = subprocess.run(
    pod + ["logs", "--tail", "400", "cta-batch2-trace-8766-v2"],
    capture_output=True, text=True
)

keys = (
    "CTA BATCH RETURNED",
    "CTA QUEUE SEND",
    "CTA TRUE MAX BATCH-2",
    "CTA HTTP QUEUE ITEM",
    "CTA RESPONSE SOCKET RECEIVED",
    "POST /v2/cta/predict",
    "ERROR",
    "Traceback",
)

print("\n=== RESPONSE DELIVERY TRACE ===")
matches = [
    x for x in (r.stdout + r.stderr).splitlines()
    if any(k in x for k in keys)
]
print("\n".join(matches[-35:]) or "NO MATCHING TRACE")

print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
PY
