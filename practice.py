podman run --rm -i --pull=never --user 0:0 \
  --entrypoint python3 8a501d7e7a40 - <<'PY'
import os, configparser
from pathlib import Path
from urllib.parse import urlsplit

paths = [Path("/root/.pip/pip.conf"),
         Path("/etc/pip.conf"),
         Path("/root/.config/pip/pip.conf")]

for p in paths:
    if p.is_file():
        print("CONFIG:", p)
        c = configparser.ConfigParser(interpolation=None)
        c.read(p)
        for section in c.sections():
            for key, value in c.items(section):
                if "index-url" in key:
                    print(key, "HOST:", urlsplit(value).hostname)

for key in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL"):
    if os.environ.get(key):
        print(key, "HOST:", urlsplit(os.environ[key]).hostname)
PY
