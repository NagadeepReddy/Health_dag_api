cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && podman \
--root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from pathlib import Path
root = Path("/opt/venv/lib/python3.12/site-packages/max")
for p in root.rglob("*.py"):
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if "compatible weights cannot be found" in line.lower():
            print("FILE:", p, "LINE:", i+1)
            for j in range(max(0,i-18), min(len(lines),i+12)):
                print(f"{j+1}: {lines[j]}")
'
