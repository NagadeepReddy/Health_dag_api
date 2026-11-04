cd /application1/sajjna8/rt-pzaas-v1.0 && \
V="$PWD/artifacts/v1.472-max/pzaas_max/validation" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none --memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/validation/python_deps:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
-v "$PWD:/workspace:ro" \
-v "$V:/validation:rw" \
-v /vzwhome/sajjna8:/wheels:ro \
-w /workspace \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -ec '
set -- /wheels/joblib-*.whl /wheels/scikit_learn-*.whl

for f do
    test -f "$f" || {
        echo "MISSING WHEEL: $f"
        exit 2
    }
done

/opt/venv/bin/python -m pip install \
  --no-index --no-deps --no-cache-dir \
  --target /validation/python_deps "$@"

/opt/venv/bin/python - <<'"'"'PY'"'"'
import sys, types
import einops, joblib, sklearn

print("EINOPS: PASS", einops.__version__)
print("JOBLIB: PASS", joblib.__version__)
print("SCIKIT-LEARN: PASS", sklearn.__version__)

for name in (
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.background",
    "apscheduler.triggers",
    "apscheduler.triggers.interval",
):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m

class BackgroundScheduler:
    def __init__(self, *a, **kw): pass
    def add_job(self, *a, **kw): pass
    def start(self): pass

class IntervalTrigger:
    def __init__(self, *a, **kw): pass

sys.modules["apscheduler.schedulers.background"].BackgroundScheduler = BackgroundScheduler
sys.modules["apscheduler.triggers.interval"].IntervalTrigger = IntervalTrigger

from pipeline import pipeline

print("PZAAS ORIGINAL DS IMPORT: PASS")
print("ORIGINAL DS: UNCHANGED")
print("REAL INPUT CAPTURE: NEXT")
PY
'
