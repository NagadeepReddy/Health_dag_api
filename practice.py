python3 - <<'PY'
import json, time, subprocess, urllib.request, urllib.error
from pathlib import Path

name = "cta-batch2-trace-8766-v2"
url = "http://127.0.0.1:8766"
file = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)

def diagnostics():
    r = subprocess.run(
        pod + ["logs", "--tail", "250", name],
        capture_output=True, text=True
    )
    lines = (r.stdout + r.stderr).splitlines()
    keys = (
        "CTA BATCH RETURNED", "CTA QUEUE SEND",
        "CTA TRUE MAX BATCH-2", "CTA HTTP QUEUE ITEM",
        "ModuleNotFoundError", "ImportError",
        "Traceback", "ERROR", "POST /v2/cta/predict"
    )
    matches = [x for x in lines if any(k in x for k in keys)]
    print("\n=== TARGETED TRACE ===")
    print("\n".join(matches[-25:]) or "No matching trace")

try:
    with opener.open(url + "/health", timeout=10) as r:
        assert r.status == 200
    print("MAX 8766 HEALTH: PASS", flush=True)
except Exception as e:
    print("MAX 8766 HEALTH: FAILED", repr(e))
    diagnostics()
    raise SystemExit(1)

assert file.is_file(), "STOP: CTA JSON missing"
body = file.read_bytes()
json.loads(body)

passed = 0

for n in (1, 2):
    print(f"\n=== REQUEST {n} ===", flush=True)
    start = time.monotonic()

    try:
        req = urllib.request.Request(
            url + "/v2/cta/predict",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with opener.open(req, timeout=240) as r:
            output = json.load(r)
            assert r.status == 200

        prediction = output["jsonData"]["prediction"]
        assert isinstance(prediction["offerList"], list)

        passed += 1
        print("HTTP 200: PASS", flush=True)
        print("LATENCY:", round(time.monotonic()-start, 2), "seconds")

    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print(e.read(1500).decode(errors="replace"))
        break

    except Exception as e:
        print("FAILED:", repr(e))
        break

print(f"\nSEQUENTIAL RESULTS: {passed}/2", flush=True)
diagnostics()

print("\nORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("NO FILES MODIFIED")
PY
