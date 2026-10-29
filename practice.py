podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --network none --read-only \
  --memory 512m --pids-limit 32 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
from pathlib import Path

root = Path("/opt/venv/lib/python3.12/site-packages/max")
files = [
    root / "serve/api_server.py",
    root / "serve/config.py",
    root / "entrypoints/pipelines.py",
]

terms = (
    "include_router", "ROUTES[", "api_type",
    "APIType.KSERVE", "APIType.OPENAI",
)

for p in files:
    if not p.is_file():
        continue
    lines = p.read_text(errors="replace").splitlines()
    print("\nFILE:", p)
    matches = [
        i for i, line in enumerate(lines)
        if any(t in line for t in terms)
    ]
    for i in matches[:20]:
        for j in range(max(0, i-1), min(len(lines), i+2)):
            print(f"{j+1}: {lines[j]}")
        print("---")

print("CHECK COMPLETE — NO FILES MODIFIED")
print("MAX SERVER NOT STARTED")
PY
