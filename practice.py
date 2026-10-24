cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import inspect; from max.pipelines.lib import PipelineModel; print("PIPELINE MODEL:", inspect.signature(PipelineModel)); print("REQUIRED METHODS:", [(n, str(inspect.signature(v))) for n,v in inspect.getmembers(PipelineModel) if getattr(v,"__isabstractmethod__",False)])'
