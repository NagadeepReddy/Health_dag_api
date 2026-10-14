cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import os, subprocess, sys
from urllib.parse import urlsplit

p = subprocess.run(
    [sys.executable, "-m", "pip", "config", "list"],
    capture_output=True, text=True
)

entries = []
for line in p.stdout.splitlines():
    if "index-url" in line.lower() and "=" in line:
        entries.append(line.split("=", 1)[1].strip().strip("'\""))

for key in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL"):
    if os.getenv(key):
        entries.append(os.environ[key])

print("CONFIGURED PACKAGE REPOSITORIES:")
if entries:
    for value in sorted(set(entries)):
        print(urlsplit(value).hostname or "Non-URL configuration")
else:
    print("NONE — internal repository needed")

print("NO FILES MODIFIED")
PY
