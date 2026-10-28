cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/maxserve_cta_extension")

for name in ("cta_router.py", "cta_http_pipeline.py"):
    p = base / name
    source = p.read_text()
    ast.parse(source)
    lines = source.splitlines()

    print(f"\n=== {name} ===")
    for i, line in enumerate(lines, 1):
        if any(x in line for x in (
            "_engine_queue",
            "EngineQueue(",
            "super().__init__",
            "__aenter__",
            "_CTA_ACTIVE_ENGINES",
            "response_worker",
            "open_channel",
            "CTA ACTIVE RECEIVER QUEUE SELECTED",
        )):
            print(f"{i}: {line.strip()}")

print("\n=== CHECK ===")
print("SOURCE SYNTAX: PASS")
print("NO FILES MODIFIED")
print("MAX NOT STARTED")
PY
