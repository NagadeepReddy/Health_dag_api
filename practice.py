cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()

old = """        scheduler_zmq_configs,
    ):"""
new = """        scheduler_zmq_configs,
        tokenizer=None,
        lora_queue=None,
    ):"""

if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s)
else:
    assert "tokenizer=None," in s and "lora_queue=None," in s, "Unexpected constructor; no changes made"

py_compile.compile(str(p), doraise=True)
print("CTA LIFECYCLE CONSTRUCTOR FIX: SYNTAX PASS")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from maxserve_cta_extension.cta_http_pipeline import CTANativeHTTPPipeline as P; inspect.signature(P).bind(model_name="cta", worker_monitor=None, scheduler_zmq_configs=None, tokenizer=None, lora_queue=None); print("CTA MAX LIFECYCLE ARGUMENTS: PASS")'
