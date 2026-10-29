podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 512m --pids-limit 32 \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
from pathlib import Path

root = Path("/opt/venv/lib/python3.12/site-packages/max")

for name in ("serve/api_server.py", "serve/config.py", "entrypoints/pipelines.py"):
    p = root / name
    print("\nFILE:", name, "EXISTS:", p.is_file())
    if not p.is_file():
        continue

    lines = p.read_text(errors="replace").splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if any(term in line for term in (
            "include_router", "ROUTES[", "APIType.KSERVE",
            "APIType.OPENAI", "prefix=", "api_type"
        ))
    ]

    for i in matches[:15]:
        for j in range(max(0, i-2), min(len(lines), i+3)):
            print(f"{j+1}: {lines[j]}")
        print("---")

print("\nROUTER CHECK COMPLETE")
print("FILES MODIFIED: NONE")
PY
