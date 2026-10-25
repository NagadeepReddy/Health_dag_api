P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P cp cta-native-live:/opt/venv/lib/python3.12/site-packages/max/serve/process_control.py /tmp/cta_process_control.py

grep -n -A 35 -E 'class ProcessMonitor|def is_healthy|def set_started|def until_healthy' /tmp/cta_process_control.py
