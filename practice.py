cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from max.serve.scheduler import queues
from max.interfaces.task import PipelineTask

rid = getattr(queues, "RequestID", None)
cfg = queues.SchedulerZmqConfigs(PipelineTask.TEXT_GENERATION)

print("REQUEST ID TYPE:", rid)
print("REQUEST ID FIELDS:", getattr(rid, "__struct_fields__", None))
print("REQUEST ID ANNOTATIONS:", getattr(rid, "__annotations__", None))
try:
    print("REQUEST ID SIGNATURE:", inspect.signature(rid))
except (TypeError, ValueError):
    pass

print("RESPONSE QUEUE CONFIG:", vars(cfg.response_queue_config))
print("REQUEST ID CHECK: COMPLETE")
PY
