cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none --memory=8g \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -c '
import json, multiprocessing as mp, queue, time
from pathlib import Path
from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler

body = json.loads(Path("/workspace/artifacts/v1.167/samples/sanity_input.json").read_text())
pipeline = CTAFactoryWrapper(dict)()
qin, qout, qcancel = mp.Queue(), mp.Queue(), mp.Queue()
scheduler = CTANativeScheduler(pipeline.cta_adapter, qin, qout, qcancel)
qin.put({"request_id": "cta-native-smoke", "body": body})

for attempt in range(120):
    scheduler.run_iteration()
    try:
        result = qout.get_nowait()
        print("CTA NATIVE SCHEDULER RESULT:", result, flush=True)
        break
    except queue.Empty:
        time.sleep(0.5)
else:
    print("CTA NATIVE SCHEDULER: NO RESPONSE", flush=True)
'
