cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e modelId=cta-native-smoke \
  -e expThrottleLabel=T \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local - <<'PY'
import json
import multiprocessing as mp
import queue
import time
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler

body = json.loads(
    Path("artifacts/v1.167/samples/sanity_input.json").read_text()
)

def fix(obj):
    if isinstance(obj, dict):
        if obj.get("webinteraction_name") is None:
            obj["webinteraction_name"] = ""
        for k, v in list(obj.items()):
            if k == "category" and v == "Smartphones":
                obj[k] = "Tiles"
            else:
                fix(v)
    elif isinstance(obj, list):
        for v in obj:
            fix(v)

fix(body)

pipeline = CTAFactoryWrapper(dict)()
qin, qout, qcancel = mp.Queue(), mp.Queue(), mp.Queue()
scheduler = CTANativeScheduler(
    pipeline.cta_adapter, qin, qout, qcancel
)

qin.put({"request_id": "cta-native-smoke", "body": body})

for attempt in range(180):
    scheduler.run_iteration()
    try:
        response = qout.get_nowait()
        item = response.get("cta-native-smoke")
        payload = getattr(getattr(item, "result", None), "result", None)
        if isinstance(payload, dict) and "error" not in payload:
            print("CTA NATIVE SCHEDULER: PASS", flush=True)
            print(json.dumps(payload, default=str)[:1000])
        else:
            print("CTA NATIVE SCHEDULER: FAIL", flush=True)
            print(str(response)[:1200])
        break
    except queue.Empty:
        time.sleep(0.5)
else:
    print("CTA NATIVE SCHEDULER: NO RESPONSE", flush=True)
PY
