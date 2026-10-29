cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
C=/application1/cta_max_native_release_candidate_20261028
NAME=cta-native-mojo-test
LOG="$BASE/native_live_http_mojo_fix.log"
OUT="$BASE/native_live_http_mojo_response.json"
INPUT=artifacts/v1.168-max/cta_native_adjusted_sanity_input.json

if [ -e "$LOG" ] || [ -e "$OUT" ]; then
  echo "STOP: Test outputs already exist"
elif [ ! -f "$C/cta_native_launcher.py" ] || \
     [ ! -f "$INPUT" ] || \
     [ ! -d artifacts/v1.168-max/cta_native_model ]; then
  echo "STOP: Required existing files missing"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 20971520 ]; then
  echo "STOP: Available RAM below 20 GiB"
elif ss -H -ltn '( sport = :18080 )' | grep -q .; then
  echo "STOP: Port 18080 occupied"
else
  timeout -s TERM -k 10s 450s \
    podman --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm --pull=never --name "$NAME" \
    --network=bridge -p 127.0.0.1:18080:8000 \
    --read-only --log-driver=none \
    --memory=16g --memory-swap=16g \
    --cpus=4 --pids-limit=256 \
    --tmpfs /tmp:rw,size=1g,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -v "$C:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -w /workspace \
    -e HOME=/tmp -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e MODULAR_CACHE_DIR=/tmp/modular \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
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
  for i in $(seq 1 48); do
    STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
      --max-time 2 http://127.0.0.1:18080/openapi.json)
    if [ "$STATUS" != 000 ]; then
      READY=1
      break
    fi
    kill -0 "$PID" 2>/dev/null || break
    sleep 5
  done

  if [ "$READY" -eq 1 ]; then
    curl -sS --max-time 300 \
      -X POST http://127.0.0.1:18080/v2/cta/predict \
      -H 'Content-Type: application/json' \
      --data-binary @"$INPUT" \
      -o "$OUT" \
      -w 'REAL CTA HTTP STATUS: %{http_code}\nLATENCY: %{time_total}s\n'

    python3 -S -B - "$OUT" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
try:
    obj = json.loads(p.read_text())
    valid = (
        isinstance(obj, dict)
        and isinstance(obj.get("jsonData"), dict)
        and isinstance(obj["jsonData"].get("prediction"), dict)
        and "offerList" in obj["jsonData"]["prediction"]
    )
    print("REAL CTA RESPONSE CONTRACT:", "PASS" if valid else "FAIL")
except Exception as e:
    print("REAL CTA RESPONSE CONTRACT: FAIL", str(e))
PY
  else
    echo "LIVE MAX SERVER: NOT READY"
  fi

  echo "=== SERVER LOG ==="
  tail -20 "$LOG"
  echo "STOP: No automatic retry"
fi
