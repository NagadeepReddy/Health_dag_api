podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 512m --pids-limit 32 \
  -v /application1/cta_max_native_release_candidate_20261028:/release:ro \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
from pathlib import Path

roots = [
    Path("/opt/venv/lib/python3.12/site-packages/max"),
    Path("/release"),
]

terms = (
    "class SchedulerZmqConfigs",
    "def model_worker_queues",
    "def msgpack_numpy_decoder",
    "def msgpack_numpy_encoder",
    "class CTAContext",
    "ZmqConfig[",
    "request_queue_config",
    "response_queue_config",
    "payload_type=",
)

for root in roots:
    for p in root.rglob("*.py"):
        if root.name == "max" and not any(
            s in str(p) for s in
            ("interfaces", "scheduler/queues.py", "queue/zmq_queue.py")
        ):
            continue

        lines = p.read_text(errors="replace").splitlines()
        hits = [
            i for i, line in enumerate(lines)
            if any(term in line for term in terms)
        ]

        if not hits:
            continue

        print("\nFILE:", p)
        shown = set()

        for i in hits[:12]:
            for j in range(max(0, i-2), min(len(lines), i+9)):
                if j not in shown:
                    print(f"{j+1}: {lines[j]}")
                    shown.add(j)

print("\nQUEUE SCHEMA CHECK COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX NOT STARTED")
PY
