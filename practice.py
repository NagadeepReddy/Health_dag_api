cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
C=/application1/cta_max_native_release_candidate_20261028
NAME=cta-native-http-final
LOG="$BASE/native_live_http_final.log"
OUT="$BASE/native_live_http_response.json"
INPUT=artifacts/v1.168-max/cta_native_adjusted_sanity_input.json

if [ -e "$LOG" ] || [ -e "$OUT" ]; then
  echo "STOP: Existing test output must be preserved"
elif [ ! -f "$C/cta_native_launcher.py" ] || \
     [ ! -f artifacts/v1.168-max/cta_native_model/config.json ] || \
     [ ! -f "$INPUT" ]; then
  echo "STOP: Required launcher, model configuration, or real JSON missing"
elif [ "$(df -PB1 /application1 | awk 'NR==2 {print $4}')" -lt 10737418240 ]; then
  echo "STOP: Less than 10 GiB free on /application1"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ]; then
  echo "STOP: Less than 20 GiB available RAM"
elif ss -H -ltn '( sport = :18080 )' | grep -q .; then
  echo "STOP: Test port already occupied"
else
  echo "STARTING BUILT-IN MAX SERVE — DEVELOPMENT TEST"

  timeout -s TERM -k 10s 450s \
    podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never --name "$NAME" \
    --network=bridge -p 127.0.0.1:18080:8000 \
    --read-only --log-driver=none \
    --memory=16g --memory-swap=16g \
    --cpus=4 --pids-limit=256 \
    --tmpfs /tmp:rw,size=1g,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -v "$C:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -w /workspace \
    -e HOME=/tmp -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e MODULAR_CACHE_DIR=/tmp/modular \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/workspace/artifacts/v1.168-max/utils/dependency-utils \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local \
    -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
    --devices cpu \
    --model-path /workspace/artifacts/v1.168-max/cta_native_model \
    --port 8000 > "$LOG" 2>&1 &

  PID=$!
  trap 'podman --root /application1/podman/storage --runroot /run/containers/storage stop --time 5 "$NAME" >/dev/null 2>&1 || true; wait "$PID" 2>/dev/null || true' EXIT

  READY=0
  for i in $(seq 1 36); do
    STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
      --max-time 3 -X POST http://127.0.0.1:18080/v2/cta/probe)
    if [ "$STATUS" = 200 ]; then
      READY=1
      break
    fi
    kill -0 "$PID" 2>/dev/null || break
    sleep 5
  done

  if [ "$READY" -ne 1 ]; then
    echo "LIVE SERVER NOT READY"
    tail -20 "$LOG"
  else
    echo "LIVE MAX SERVE: READY"
    curl --silent --show-error --max-time 300 \
      -X POST http://127.0.0.1:18080/v2/cta/predict \
      -H 'Content-Type: application/json' \
      --data-binary @"$INPUT" \
      -o "$OUT" \
      -w 'REAL CTA HTTP STATUS: %{http_code}\nTOTAL SECONDS: %{time_total}\n'

    python3 -S -B - "$OUT" <<'PY'
import json, sys
from pathlib import Path

p = Path(sys.argv[1])
if not p.is_file():
    print("REAL CTA RESPONSE: NOT RECEIVED")
else:
    try:
        obj = json.loads(p.read_text())
        valid = isinstance(obj, dict) and isinstance(obj.get("jsonData"), dict) and "prediction" in obj["jsonData"]
        print("REAL CTA JSON CONTRACT:", "PASS" if valid else "NOT VERIFIED")
        print("RESPONSE KEYS:", list(obj) if isinstance(obj, dict) else type(obj).__name__)
    except Exception as e:
        print("REAL CTA JSON: FAILED", str(e))
PY
  fi

  echo "=== SERVER LOG ==="
  tail -15 "$LOG"
fi
