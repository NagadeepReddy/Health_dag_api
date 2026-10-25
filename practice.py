cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py")
s = p.read_text()
old = '    task_name="cta_response_worker",\n'
assert s.count(old) == 1, "Expected argument not found"
s = s.replace(old, "", 1)
compile(s, str(p), "exec")
p.write_text(s)
print("CTA RESPONSE WORKER SIGNATURE: FIXED")
PY

P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P run -d --replace --name cta-native-live \
  --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py

sleep 12
$P logs --tail 45 cta-native-live 2>&1 | grep -E \
'CTA_RESPONSE_WORKER_STARTED|startup complete|Uvicorn running|Traceback|ERROR|TypeError'
