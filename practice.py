PODMAN=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-clean-native-batch2

echo "=== HTTP PORT OWNER ==="
"${PODMAN[@]}" ps --format '{{.Names}} | {{.Ports}}' | grep -E '18767|cta-clean' || true

echo "=== CLEAN CONTAINER PORT ==="
"${PODMAN[@]}" port "$NAME" 2>&1

echo "=== ACTUAL WEIGHT READ ==="
"${PODMAN[@]}" exec "$NAME" /opt/venv/bin/python -B -c '
from pathlib import Path
import numpy as np
p = Path("/batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy")
print("EXISTS:", p.is_file())
print("RESOLVED:", p.resolve())
a = np.load(p, allow_pickle=False)
print("NUMPY LOAD: PASS")
print("SHAPE:", a.shape)
'
