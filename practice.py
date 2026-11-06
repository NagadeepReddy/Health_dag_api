
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
SOURCE="$ROOT/bin/run_max_model.sh"
TARGET="$ROOT/bin/run_max_model_shared.sh"
PACKAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"

test -f "$SOURCE"
test -d "$PACKAGE/model"
test -d "$PACKAGE/runtime/python_deps"

for name in typed_queue scheduler_hooks router_contract worker_lifecycle; do
  test -f "$ROOT/python/max_runtime_shared/${name}.py"
done

if [ -e "$TARGET" ]; then
  echo "STOP: Shared launcher already exists; nothing overwritten"
  exit 1
fi

python3 - "$SOURCE" "$TARGET" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])

code = source.read_text()

changes = [
    (
        'DEPENDENCY_DIR="$PACKAGE/runtime/python_deps"\n',
        'DEPENDENCY_DIR="$PACKAGE/runtime/python_deps"\n'
        'SHARED_PYTHON="$(cd "$(dirname "${BASH_SOURCE[0]}")/../python" && pwd -P)"\n'
        'test -f "$SHARED_PYTHON/max_runtime_shared/typed_queue.py" || {\n'
        '  echo "STOP: Shared Python runtime missing"\n'
        '  exit 1\n'
        '}\n',
    ),
    (
        '  -v "$DEPENDENCY_DIR:/shared_deps:ro" \\\n',
        '  -v "$DEPENDENCY_DIR:/shared_deps:ro" \\\n'
        '  -v "$SHARED_PYTHON:/shared_runtime:ro" \\\n',
    ),
    (
        '  -e "PYTHONPATH=$MODEL_PYTHONPATH" \\\n',
        '  -e "PYTHONPATH=/shared_runtime:$MODEL_PYTHONPATH" \\\n',
    ),
]

for old, new in changes:
    count = code.count(old)
    if count != 1:
        raise SystemExit(
            f"STOP: Expected one launcher insertion point, found {count}"
        )
    code = code.replace(old, new, 1)

with target.open("x") as f:
    f.write(code)

target.chmod(0o755)

print("OPT-IN SHARED LAUNCHER: CREATED")
print("ORIGINAL LAUNCHER: UNCHANGED")
print("SHARED PYTHON MOUNT: CONFIGURED")
print("SHARED PYTHONPATH: CONFIGURED")
PY

bash -n "$TARGET"

if id sajjna8 >/dev/null 2>&1; then
  chown sajjna8:"$(id -gn sajjna8)" "$TARGET"
fi

echo
echo "=== SHARED LAUNCHER PREFLIGHT ==="

bash "$TARGET" check "$PACKAGE"

echo
echo "=== RESULT ==="
echo "SHARED LAUNCHER SYNTAX: PASS"
echo "SHARED LIBRARY MOUNT: CONFIGURED"
echo "ORIGINAL WORKING LAUNCHER: UNCHANGED"
echo "MODEL HANDOFFS: UNCHANGED"
echo "RUNNING CONTAINERS: UNCHANGED"
echo "NO DUPLICATE MAX HOOKS INSTALLED"
echo "NEXT: ISOLATED SHARED QUEUE INTEGRATION"
SH
