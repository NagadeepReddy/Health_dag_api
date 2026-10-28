timeout 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --memory=512m --cpus=1 --pids-limit=64 \
  --network=none --read-only --log-driver=none \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=64m,mode=1777 \
  -e PYTHONPATH=/cta \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v /application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max:/cta:ro \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local \
  -c 'import sys,runpy; from maxserve_cta_extension.cta_architecture_registration import register_cta_architecture; register_cta_architecture(); print("CTA REGISTRATION: PASS",flush=True); sys.argv=["max.entrypoints.pipelines","serve","--model-path","/cta/cta_native_model","--devices","cpu","--quantization-encoding","float32","--pretty-print-config"]; runpy.run_module("max.entrypoints.pipelines",run_name="__main__")'
