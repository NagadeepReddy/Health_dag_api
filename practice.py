P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P cp cta-native-live:/opt/venv/lib/python3.12/site-packages/max/serve/pipelines/model_worker.py /tmp/cta_model_worker.py

grep -n -C 12 -E \
'def start_model_worker|ProcessMonitor|worker_monitor|exitcode|is_alive|spawn' \
/tmp/cta_model_worker.py | head -150
