podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 512m --pids-limit 32 \
  -v /application1/cta_max_native_release_candidate_20261028:/release:ro \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
from pathlib import Path

base = Path("/opt/venv/lib/python3.12/site-packages/max")

targets = [
    (base / "serve/queue/zmq_queue.py",
     ("get_nowait", "decode", "deserialize", "type")),
    (base / "interfaces/queue.py",
     ("BackgroundQueueDrainer", "get_nowait", "drain")),
    (base / "serve/pipelines/model_worker.py",
     ("run_iteration", "scheduler", "queue")),
    (Path("/release/cta_native_scheduler.py"),
     ("ZmqConfig", "run_iteration", "CTAContext", "request_id")),
    (Path("/release/cta_context.py"),
     ("class CTAContext", "type", "request_id")),
    (Path("/release/cta_http_pipeline.py"),
     ("ZmqConfig", "open_channel", "request_queue")),
]

for path, terms in targets:
    print("\n=== FILE:", path.name, "===")
    if not path.is_file():
        print("NOT PRESENT")
        continue

    lines = path.read_text(errors="replace").splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(term in line for term in terms):
            selected.update(range(max(0, i-2), min(len(lines), i+5)))

    for i in sorted(selected)[:100]:
        print(f"{i+1}: {lines[i]}")

print("\nQUEUE CONTRACT CHECK COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX NOT STARTED")
PY
