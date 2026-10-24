cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import inspect
import importlib

queues = importlib.import_module("max.serve.scheduler.queues")

print("=== MAX REQUEST TYPE SELECTION ===")
fn = queues._get_request_type_from_pipeline_task
print(inspect.getsource(fn))

print("\n=== ACTUAL PIPELINE TASK TYPE ===")
PipelineTask = fn.__globals__.get("PipelineTask")

if PipelineTask is None:
    print("Task enum not in function globals")
else:
    print("MODULE:", PipelineTask.__module__)
    print("TASKS:", list(PipelineTask))

    for task in PipelineTask:
        try:
            request_type = fn(task)
            print("TASK:", task, "REQUEST TYPE:", request_type)
        except Exception as exc:
            print("TASK:", task, "ERROR:", str(exc))

print("\nQUEUE CONTRACT CHECK COMPLETE")
PY
