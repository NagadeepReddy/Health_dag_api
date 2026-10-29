cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate

test -s "$CAND/cta_max/run_batch2_contract.py"

timeout 60s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 1g --cpus 1 --pids-limit 64 \
  --read-only \
  --tmpfs /tmp:rw,size=64m \
  -e HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH="/workspace/artifacts/v1.168-max:$CAND" \
  -v "$PWD:/workspace:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -B - <<'PY'
import cta_max
from pathlib import Path

print("CTA PACKAGE:", list(cta_max.__path__))

candidate = (
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

if candidate not in cta_max.__path__:
    cta_max.__path__.append(candidate)

from cta_max.run_batch2_contract import pack_two_requests

assert callable(pack_two_requests)
print("CONTAINER CONTRACT IMPORT: PASS")
print("CONTRACT LOCATION:", Path(
    __import__(
        "cta_max.run_batch2_contract",
        fromlist=[""]
    ).__file__
))
print("NO FILES MODIFIED")
PY
SH
