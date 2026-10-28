cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout 20s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=16 \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/cta:ro" \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -S -B - <<'PY'
from pathlib import Path

base = Path("/opt/venv/lib/python3.12/site-packages/max")
targets = [
    (Path("/cta/cta_router.py"), ["open_channel", "response_queue.get", "RequestID", "request_id"]),
    (Path("/cta/cta_native_scheduler.py"), ["response", "RequestID", "send", "result"]),
]

for folder in [base / "serve/queue", base / "serve/scheduler"]:
    if folder.exists():
        for p in folder.rglob("*.py"):
            s = p.read_text(errors="replace")
            if any(x in s for x in (
                "async def response_worker",
                "def response_worker",
                "class EngineQueue",
                "class ZmqPullSocket",
            )):
                targets.append((p, [
                    "response_worker", "open_channel",
                    "response_queue", "get_nowait",
                    "RequestID", "recv", "send",
                ]))

for p, terms in targets:
    print(f"\n========== {p} ==========")
    if not p.exists():
        print("MISSING")
        continue
    lines = p.read_text(errors="replace").splitlines()
    selected = set()
    for i, line in enumerate(lines):
        if any(t in line for t in terms):
            selected.update(range(max(0, i-4), min(len(lines), i+9)))
    for i in sorted(selected):
        print(f"{i+1:4}: {lines[i][:180]}")

print("\nSOURCE DIAGNOSTIC COMPLETE — NO CHANGES")
PY
