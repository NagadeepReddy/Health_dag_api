podman run --rm --entrypoint /bin/bash \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -lc 'python - <<'"'"'PY'"'"'
from pathlib import Path

root = Path("/opt/venv/lib/python3.12/site-packages/max")
files = [
    root / "serve/api_server.py",
    root / "serve/config.py",
    root / "pipelines/lib/config.py",
]

for p in files:
    print("\nFILE:", p, "EXISTS:", p.exists())
    if not p.exists():
        continue
    for number, line in enumerate(p.read_text().splitlines(), 1):
        if any(x in line for x in (
            "PipelineTask.", "APIType.", "custom_architectures",
            "_import_custom_architectures", "predict_raw"
        )):
            print(f"{number}: {line.strip()[:160]}")
PY'
