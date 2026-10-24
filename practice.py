cd /application1/sajjna8/rt-pzaas-cta-offers-v1

MODEL=$(find artifacts/v1.168-max \
  -path '*/cta_native_model/config.json' \
  -print -quit)

if [ -z "$MODEL" ]; then
  echo "CTA model config not found"
else
  timeout 60s podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never --network=none \
    -v "$PWD:/workspace:Z" \
    -e PYTHONPATH=/workspace/artifacts/v1.168-max \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -u -m maxserve_cta_extension.cta_native_launcher \
    --model-path "/workspace/${MODEL%/config.json}" \
    --port 8000

  echo "STARTUP EXIT CODE: $?"
fi
