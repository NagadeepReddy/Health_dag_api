cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none --memory 2g \
-v "$PWD:/workspace:ro" \
-w /workspace \
--entrypoint python3 localhost/cta-max-faiss:local - <<'PY'
import ast, importlib.util, sys
from pathlib import Path

roots = [
    Path("artifacts/v1.472/core-artifact"),
    Path("artifacts/v1.472/utils/dependency-utils")
]

modules = set()
local = set()
for root in roots:
    for p in root.rglob("*.py"):
        local.add(p.stem)
        try:
            tree = ast.parse(p.read_text(errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                modules.update(x.name.split(".")[0] for x in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                modules.add(n.module.split(".")[0])

missing = []
for name in sorted(modules - local - sys.stdlib_module_names):
    try:
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    except (ImportError, ValueError, ModuleNotFoundError):
        missing.append(name)

print("=== MISSING DS RUNTIME IMPORTS ===")
for name in missing:
    print("MISSING:", name)
print("TOTAL:", len(missing))
print("RUNTIME AUDIT: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
PY

echo "=== LOCAL EINOPS / APSCHEDULER PACKAGES ==="
find /application1/sajjna8 /opt/venv \
  -maxdepth 7 \
  \( -type d \( -name einops -o -name apscheduler \) \
  -o -type f \( -iname 'einops*.whl' -o -iname 'apscheduler*.whl' \) \) \
  -print 2>/dev/null | head -30
