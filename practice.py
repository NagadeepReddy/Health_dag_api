cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -u

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/distinct_batch2_explicit_execution.log"

test -s "$DEV/run_distinct_batch2_live_max_inference.py" || exit 1
test -s "$DEV/second_real_cta_model_in.pt" || exit 1
test -s artifacts/v1.168-max/cta_max/real_sanity_model_in.pt || exit 1

if [ -e "$LOG" ]; then
  echo "STOP: Preserve existing log $LOG"
  exit 1
fi

echo "=== RUNNING REAL DISTINCT-INPUT MAX BATCH-2 ==="

timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e CTA_SECOND_MODEL_INPUT=/batch2/second_real_cta_model_in.pt \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168-max" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -c '
import runpy
import torch

print("EXPLICIT REAL MAX BATCH-2 START", flush=True)

ns = runpy.run_path(
    "/batch2/run_distinct_batch2_live_max_inference.py"
)

fn = ns.get("infer_max_live")
assert callable(fn), "STOP: infer_max_live function missing"

model_in = torch.load(
    "/workspace/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt",
    map_location="cpu",
    weights_only=True
)

print("CALLING ACTUAL MAX INFERENCE", flush=True)
result = fn(model_in)

if result is None:
    print("FUNCTION RETURNED NONE: CHECK INFERENCE OUTPUT ABOVE", flush=True)
elif hasattr(result, "shape"):
    print("RETURNED SHAPE:", result.shape, flush=True)
elif isinstance(result, (list, tuple)):
    print("RETURNED OUTPUT SHAPES:",
          [getattr(x, "shape", type(x).__name__) for x in result],
          flush=True)
else:
    print("RETURNED TYPE:", type(result).__name__, flush=True)

print("EXPLICIT MAX FUNCTION COMPLETED", flush=True)
' > "$LOG" 2>&1

RC=$?

echo "=== EXECUTION RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
echo "LOG LINES: $(wc -l < "$LOG")"
echo "=== FINAL OUTPUT ==="
tail -65 "$LOG"

if [ "$RC" -ne 0 ]; then
  echo "DISTINCT BATCH-2: FAIL"
  exit "$RC"
fi

echo "DISTINCT BATCH-2 FUNCTION: COMPLETED"
echo "RESULT VALIDATION: CHECK OUTPUT ABOVE"
echo "ORIGINAL DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
