python - <<'PY'
from pathlib import Path
import ast
import re

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "grecbase_fusion_verified_wiring_trial.py"
)

source = p.read_text()
names = [
    "seq", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

pattern = re.compile(
    r'(?P<indent>^[ \t]*)'
    r'# TRIAL: wire the eight verified branch outputs into fusion[^\n]*\n'
    r'(?P=indent)outs\s*=\s*ops\.stack\(\[\s*\n'
    r'(?P<body>.*?)'
    r'(?P=indent)\],\s*axis=1\)',
    re.MULTILINE | re.DOTALL
)

matches = list(pattern.finditer(source))

if len(matches) != 1:
    raise SystemExit(
        "STOP: Expected trial stack not found exactly once. "
        "No files changed."
    )

match = matches[0]

actual = re.findall(
    r'^\s*([A-Za-z_]\w*),\s*$',
    match.group("body"),
    re.MULTILINE
)

if actual != names:
    raise SystemExit(
        f"STOP: Unexpected branch list: {actual}. "
        "No files changed."
    )

indent = match.group("indent")

replacement = (
    indent + "# TRIAL: wire the eight verified branch outputs into fusion\n"
    + indent + "outs = ops.stack([\n"
    + "".join(
        indent + f"    ops.reshape({name}, [1, 256]),\n"
        for name in names
    )
    + indent + "], axis=1)"
)

updated = (
    source[:match.start()]
    + replacement
    + source[match.end():]
)

ast.parse(updated)
p.write_text(updated)

print("TRIAL STACK RANK CORRECTED")
print("EIGHT BRANCH ORDER UNCHANGED")
print("ORIGINAL MAX / PYTORCH / DS CODE UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_verified_wiring_trial.py
