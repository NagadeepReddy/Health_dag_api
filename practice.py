podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=4g --cpus=2 --pids-limit=128 \
  --network=none --read-only \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /root:rw,size=64m \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1:/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e HOME=/tmp -e TMPDIR=/tmp \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -c 'import faulthandler; faulthandler.dump_traceback_later(15); from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry; install_cta_spawn_entry(); print("WORKER REGISTRATION COMPLETE", flush=True)'
