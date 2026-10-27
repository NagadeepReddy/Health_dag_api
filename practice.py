timeout -s TERM -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=4g --cpus=2 --pids-limit=128 \
  --network=none --read-only \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /root:rw,size=64m \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=128m \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e HOME=/tmp -e TMPDIR=/tmp \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -c 'import faulthandler; faulthandler.dump_traceback_later(20); from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture; register_cta_architecture(); print("CTA ARCHITECTURE REGISTRATION: PASS", flush=True)'
