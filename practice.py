podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --network none --read-only \
  --memory 512m --pids-limit 32 \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -S -B -c '
from pathlib import Path
root = Path("/opt/venv/lib/python3.12/site-packages/max")
found = 0
for p in root.rglob("*.py"):
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if "compatible weights cannot be found" in line:
            print("FILE:", p)
            for j in range(max(0, i-18), min(len(lines), i+12)):
                print(f"{j+1}: {lines[j]}")
            found += 1
print("WEIGHT REJECTION LOCATIONS:", found)
print("MODEL NOT STARTED; DS CODE UNCHANGED")
'
