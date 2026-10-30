python3 - <<'PY'
import json, time, subprocess, urllib.request, urllib.error
from pathlib import Path

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
name = "cta-batch2-trace-8766-v2"
url = "http://127.0.0.1:8766"
file = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")

def logs():
    r = subprocess.run(pod + ["logs", "--tail", "400", name],
                       capture_output=True, text=True)
    keys = ("CTA BATCH RETURNED", "CTA QUEUE SEND",
            "CTA TRUE MAX BATCH-2", "CTA HTTP QUEUE ITEM",
            "POST /v2/cta/predict", "ModuleNotFoundError",
            "ERROR", "Traceback")
    matches = [x for x in (r.stdout+r.stderr).splitlines()
               if any(k in x for k in keys)]
    print("\n=== MAX RESPONSE TRACE ===", flush=True)
    print("\n".join(matches[-30:]) or "NO MATCHING TRACE")

r = subprocess.run(pod + ["inspect", name],
                   capture_output=True, text=True, check=True)
info = json.loads(r.stdout)[0]
print("CONTAINER:", info["State"]["Status"])
print("MEMORY LIMIT GB:", round(info["HostConfig"]["Memory"]/1024**3, 2))

if info["State"]["Status"] != "running":
    logs()
    raise SystemExit("STOP: Isolated server not running")

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

try:
    with opener.open(url + "/health", timeout=10) as r:
        assert r.status == 200
    print("MAX 8766 HEALTH: PASS")
except Exception as e:
    print("HEALTH FAILED:", repr(e))
    logs()
    raise SystemExit(1)

assert file.is_file(), "STOP: Previously tested JSON missing"
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
        with opener.open(req, timeout=210) as r:
            output = json.load(r)
            assert r.status == 200

        prediction = output["jsonData"]["prediction"]
        assert isinstance(prediction["offerList"], list)

        passed += 1
        print("RESULT: PASS HTTP 200", flush=True)
        print("LATENCY:", round(time.monotonic()-start, 2), "seconds")

    except urllib.error.HTTPError as e:
        print("RESULT: HTTP", e.code)
        print("ERROR BODY:", e.read(1200).decode(errors="replace"))
        break
    except Exception as e:
        print("RESULT: FAILED", repr(e), flush=True)
        break

print(f"\nSEQUENTIAL RESULTS: {passed}/2")
logs()
print("\nORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
