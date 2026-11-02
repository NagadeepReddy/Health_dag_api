python3 - <<'PY'
from pathlib import Path

root = Path("/application1")
b = root / "sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev"
c = root / "CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension"

for label, base in [("BPLAN", b), ("CTA", c)]:
    print(f"\n========== {label} REQUEST AND QUEUE ==========")

    for name in ("queue_compat", "http_pipeline", "context", "router"):
        matches = sorted(base.rglob(f"*{name}*.py"))
        for p in matches[:3]:
            print(f"\n--- {p.name} ---")
            lines = p.read_text(errors="replace").splitlines()

            if name in ("queue_compat", "context"):
                selected = range(min(len(lines), 140))
            else:
                keywords = (
                    "request_queue", "put_nowait", "enqueue",
                    "context", "requestid", "request_id",
                    "serialize", "queue_response", "type="
                )
                hits = [
                    i for i, line in enumerate(lines)
                    if any(k in line.lower() for k in keywords)
                ]
                selected = sorted({
                    j for i in hits[:25]
                    for j in range(max(0, i-2), min(len(lines), i+4))
                })

            for i in selected:
                print(f"{i+1:4}: {lines[i][:180]}")
PY
