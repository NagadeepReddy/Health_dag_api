podman run --rm --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import os, subprocess, urllib.parse

r = subprocess.run(
    ["python", "-m", "pip", "config", "list"],
    capture_output=True, text=True
)

print("PIP PACKAGE SOURCES:")
for key in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL"):
    value = os.getenv(key, "")
    print(key, urllib.parse.urlsplit(value).hostname or "NOT SET")

for line in r.stdout.splitlines():
    if "index-url" in line.lower():
        value = line.split("=", 1)[-1].strip().strip("'\"")
        print("CONFIGURED INDEX:", urllib.parse.urlsplit(value).hostname or "NOT SET")
PY
