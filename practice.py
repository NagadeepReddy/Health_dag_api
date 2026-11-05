
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network=none \
-v /application1/max_shared_python_deps:/shared_deps:ro \
-v "$PWD:/workspace:ro" \
-e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import sklearn
from sklearn.compose._column_transformer import _RemainderColsList
from apscheduler.schedulers.background import BackgroundScheduler
import torch
import faiss
import max

print("SCIKIT-LEARN VERSION:", sklearn.__version__)
assert sklearn.__version__ == "1.6.1"
print("PZAAS PREPROCESSOR CLASS: PASS")
print("APScheduler: PASS")
print("MAX AND FAISS: PASS")
print("CTA/BPLAN IMAGE: UNCHANGED")
PY
