P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P exec cta-native-live sh -c \
"grep -Rn -A 35 -E 'class ProcessMonitor|def is_healthy|def set_started|def until_healthy' /opt/venv/lib/python3.12/site-packages/max/serve/process_control.py"
