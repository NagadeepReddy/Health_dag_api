
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
W=/vzwhome/sajjna8/pzaas_wheels
D=/application1/max_shared_python_deps

test -d "$W"
mkdir -p "$D/sklearn161"

echo "=== INSTALL SCIKIT-LEARN 1.6.1 OFFLINE ==="

"${P[@]}" run --rm --pull=never --network=none \
  -v "$W:/wheels:ro" \
  -v "$D:/shared_deps" \
  -v "$PWD:/workspace:ro" \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps \
  --entrypoint /bin/sh \
  localhost/cta-max-faiss:local -ec '
    set -e

    /opt/venv/bin/python -m pip install \
      --no-index --no-deps \
      --target=/shared_deps/sklearn161 \
      /wheels/scikit_learn-1.6.1-*.whl

    /opt/venv/bin/python -c "
import sklearn
from sklearn.compose._column_transformer import _RemainderColsList
from apscheduler.schedulers.background import BackgroundScheduler
assert sklearn.__version__ == '1.6.1'
print('SCIKIT-LEARN 1.6.1: PASS')
print('PZAAS PREPROCESSOR CLASS: AVAILABLE')
print('APScheduler: PASS')
print('CTA/BPLAN IMAGE: UNCHANGED')
"
  '
SH
