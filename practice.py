cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

anchor = "            lora_queue=None,\n        )"
marker = "CTA_ENGINE_QUEUE_INIT_GUARD"

if marker not in s:
    if s.count(anchor) != 1:
        raise SystemExit("Constructor location not found. No changes made.")

    patch = '''
        # CTA_ENGINE_QUEUE_INIT_GUARD
        if getattr(self, "_engine_queue", None) is None:
            engine_queue_cls = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]
            self._engine_queue = engine_queue_cls(
                worker_monitor=worker_monitor,
                scheduler_zmq_configs=scheduler_zmq_configs,
            )
        print("CTA QUEUE INITIALIZED:", self._engine_queue is not None, flush=True)
'''
    updated = s.replace(anchor, anchor + patch, 1)
    compile(updated, str(p), "exec")
    p.write_text(updated)

print("CTA MAX QUEUE GUARD: SYNTAX PASS")
print("ORIGINAL DS CODE: UNCHANGED")
PY

timeout 150s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  > /tmp/cta_queue_init.log 2>&1

rc=$?
grep -E 'CTA QUEUE INITIALIZED|CTA ACTUAL ENGINE QUEUE|CTA NATIVE HTTP STATUS|CTA RESPONSE:|Traceback|AssertionError|ValidationError' \
  /tmp/cta_queue_init.log | tail -12
echo "E2E EXIT CODE: $rc"
