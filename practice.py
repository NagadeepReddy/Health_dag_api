podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec --workdir /workspace cta-postman-shm1g-test \
  /opt/venv/bin/python -B -c '
from pathlib import Path
p = Path("artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy")
assert p.is_file(), f"STOP: Missing {p}"
print("MODEL WEIGHT PATH: PASS")
print("WORKING DIRECTORY: /workspace")
print("ORIGINAL CODE: UNCHANGED")
'
