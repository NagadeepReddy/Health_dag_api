cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  events --stream=false \
  --since 2026-10-28T19:00:00Z \
  --until 2026-10-28T20:00:00Z \
  --filter container=cta_native_corrected_1028 \
  --format json | \
python3 -S -B -c '
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
    except ValueError:
        continue
    status = e.get("Status", e.get("status", ""))
    attrs = e.get("Attributes", e.get("attributes", {})) or {}
    print(
        "TIME:", e.get("Time", e.get("time")),
        "| EVENT:", status,
        "| SIGNAL:", attrs.get("signal", "not recorded"),
        "| EXIT:", attrs.get("exitCode", attrs.get("exit_code", "not recorded"))
    )
'
