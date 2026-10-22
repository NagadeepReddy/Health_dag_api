cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

ROOT=/application1/podman/storage
RUNROOT=/run/containers/storage

IMG=$(podman --root "$ROOT" --runroot "$RUNROOT" images \
  --format '{{.ID}} {{.Repository}}:{{.Tag}}' |
  awk '$2 ~ /modular\/max-full:latest$/ {print $1; exit}')

[ -n "$IMG" ] || { echo "MAX IMAGE ID NOT FOUND"; exit 1; }

echo "Using local image ID: $IMG"

timeout -k 5s 30s podman \
  --root "$ROOT" --runroot "$RUNROOT" \
  run --rm --pull=never \
  --network=none --memory=8g --memory-swap=8g --pids-limit=64 \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  "$IMG" \
  -u -c 'from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler; print("REAL MAX CTA FACTORY IMPORT: PASS", flush=True)'
