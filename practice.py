REPO=/application1/sajjna8/rt-pzai-bplan-v1
DEV="$REPO/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev"

DEV="$DEV" python3 - <<'PY'
import os
from pathlib import Path

p = Path(os.environ["DEV"]) / "bplan_max_model_adapter.py"
s = p.read_text()

old = "return torch.from_numpy(scores)"
new = "return torch.from_numpy(scores.copy())"

assert s.count(old) == 1, "STOP: unexpected adapter code"
p.write_text(s.replace(old, new))

print("BPLAN READ-ONLY TENSOR WARNING: FIXED")
PY

python3 -m py_compile "$DEV/bplan_max_model_adapter.py" || exit 1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
from pathlib import Path

root = Path("artifacts/v1.113").resolve()
sys.path.insert(0, str(root / "core-artifact"))
sys.path.insert(0, str(root / "utils/dependency-utils"))

try:
    import pipeline
    print("BPLAN ORIGINAL JSON PIPELINE IMPORT: PASS")
    print("PIPELINE CLASS:", hasattr(pipeline, "pipeline"))
except Exception as e:
    print("BPLAN ORIGINAL JSON PIPELINE IMPORT: BLOCKED")
    print(type(e).__name__ + ":", str(e))
    sys.exit(1)

print("ORIGINAL DS AND CTA: UNCHANGED")
PY
