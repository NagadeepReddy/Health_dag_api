cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
LOG="$DEV/native_true_batch2_kserve_verified.log"

test -s "$LOG" || {
  echo "STOP: Previous native HTTP log missing"
  exit 1
}

echo "=== LAST NATIVE SERVER STARTUP ==="

grep -niE \
'server ready|ready on|server started|starting server|shut down|shutdown|worker|initialized|api.type|kserve|exception|timeout|telemetry|error' \
"$LOG" | tail -40 || true

echo
echo "=== INSTALLED MAX ROUTING AND READINESS CONFIG ==="

TMPDIR="$DEV" timeout -k 5s 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network none \
  --read-only --memory 1g --cpus 1 --pids-limit 64 \
  --tmpfs /tmp:rw,size=64m \
  --tmpfs /root:rw,size=32m \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -I -B - <<'PY'
from pathlib import Path

root = Path(
    "/opt/venv/lib/python3.12/site-packages/max"
)

files = [
    root / "serve/config.py",
    root / "serve/api_server.py",
    root / "entrypoints/pipelines.py",
]

terms = (
    "api_types",
    "apitype",
    "kserve",
    "routes[",
    "include_router",
    "health",
    "ready",
    "environment",
    "getenv",
    "load_scheduler",
)

for path in files:
    print(f"\n=== {path.relative_to(root)} ===")

    if not path.is_file():
        print("FILE NOT FOUND")
        continue

    lines = path.read_text(errors="replace").splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(t in line.lower() for t in terms):
            selected.update(
                range(
                    max(0, i-1),
                    min(len(lines), i+3)
                )
            )

    for i in sorted(selected)[:75]:
        print(f"{i+1}: {lines[i][:180]}")

print("\nMAX CONFIG INSPECTION: COMPLETE")
print("NO MAX SERVER STARTED")
print("NO SOURCE FILES MODIFIED")
PY

echo
echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
