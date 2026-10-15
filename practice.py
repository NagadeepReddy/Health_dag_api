podman run --rm -i --pull=never \
  --entrypoint python3 8a501d7e7a40 - <<'PY'
import os, pathlib, configparser
from urllib.parse import urlsplit

paths = [
    pathlib.Path("/etc/pip.conf"),
    pathlib.Path("/root/.pip/pip.conf"),
    pathlib.Path("/root/.config/pip/pip.conf"),
]
found = False
for p in paths:
    if p.is_file():
        found = True
        print("CONFIG FILE:", p)
        c = configparser.ConfigParser()
        c.read(p)
        for section in c.sections():
            for key, value in c.items(section):
                if "index-url" in key:
                    u = urlsplit(value)
                    print(key, "HOST:", u.hostname or "NOT SET", "PATH:", u.path)
for name in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL"):
    value = os.environ.get(name)
    if value:
        found = True
        u = urlsplit(value)
        print(name, "HOST:", u.hostname, "PATH:", u.path)
print("INTERNAL PIP CONFIG:", "FOUND" if found else "NOT FOUND")
PY
