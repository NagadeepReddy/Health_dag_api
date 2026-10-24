cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.scheduler import queues
from max.pipelines.lib import PipelineTask
from maxserve_cta_extension.cta_context import CTAContext

print("=== MAX REQUEST TYPE SELECTION ===")
print(inspect.getsource(queues._get_request_type_from_pipeline_task))

print("\n=== CURRENT TASK REQUEST TYPE ===")
task = PipelineTask.TEXT_GENERATION
config = queues.SchedulerZmqConfigs(task)

print("TASK:", task)
print("DECODER CONFIG:", config.request_queue_config)
print("CTA CONTEXT:", CTAContext)
print("CTA BASE CLASSES:", CTAContext.__mro__)

print("\nCTA QUEUE CONTRACT CHECK COMPLETE")
PY
