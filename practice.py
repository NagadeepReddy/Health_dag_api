podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
import inspect
from max.serve.pipelines.model_worker import ModelWorker

src, start = inspect.getsourcelines(ModelWorker.run)
for i, line in enumerate(src):
    if any(x in line for x in (
        "model_factory(", "load_scheduler(",
        "scheduler.run", "except", "finally"
    )):
        print(f"=== LINE {start+i} ===")
        for j in range(max(0, i-5), min(len(src), i+10)):
            print(f"{start+j}: {src[j].rstrip()}")
'
