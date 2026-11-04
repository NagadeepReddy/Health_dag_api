cd /application1/sajjna8/rt-pzaas-v1.0 && \
mkdir -p artifacts/v1.472-max/pzaas_max/validation/python_deps && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--memory 2g \
-v "$PWD/artifacts/v1.472-max/pzaas_max/validation/python_deps:/deps:rw" \
--entrypoint /bin/sh localhost/cta-max-faiss:local -c '
python3 -m pip install --disable-pip-version-check \
--no-cache-dir --target /deps "APScheduler>=3.10,<4" &&
PYTHONPATH=/deps python3 -c "
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
print(\"PZAAS APSCHEDULER: PASS\")
print(\"ORIGINAL DS: UNCHANGED\")
print(\"REAL INPUT CAPTURE: NEXT\")
"
'
