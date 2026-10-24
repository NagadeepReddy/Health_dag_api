python3 - <<'PY'
from pathlib import Path

for name in ("cta_handoff_check", "cta_socket_trace", "cta_queue_fix_test"):
    p = Path(f"/tmp/{name}.log")
    if not p.exists():
        continue

    lines = p.read_text(errors="replace").splitlines()
    print(f"\n=== {name} ===")

    for term in (
        "CTA REQUEST RECEIVED",
        "CTA NATIVE RESPONSE TYPES",
        "CTA WORKER RESPONSE IDS: [RequestID",
        "CTA SOCKET RECEIVE:",
        "HTTP WAITING ID:",
        "HTTP RESPONSE ENQUEUED:",
        "CTA NATIVE HTTP STATUS:",
    ):
        matches = [x for x in lines if term in x]
        print(f"{term}: {'YES' if matches else 'NO'}")
        if matches and term in (
            "CTA WORKER RESPONSE IDS: [RequestID",
            "CTA SOCKET RECEIVE:",
        ):
            print(" ", matches[-1][:200])
PY
