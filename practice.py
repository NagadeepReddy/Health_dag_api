python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path(
    "artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py"
)
s = p.read_text()

old = '''    if key.startswith("sequence_transformer.seq_dense."):
        aliases.append(key.removeprefix("sequence_transformer."))

'''

if old not in s:
    raise SystemExit(
        "STOP: Expected incorrect alias block not found. "
        "Nothing changed."
    )

if s.count(old) != 1:
    raise SystemExit("STOP: Unexpected duplicate alias blocks.")

updated = s.replace(old, "", 1)
ast.parse(updated, filename=str(p))

backup = p.with_suffix(".py.before_seq_dense_alias_fix")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)

print("UNNECESSARY SEQ_DENSE ALIAS REMOVED")
print("TRANSFORMER .fn. MAPPING PRESERVED")
print("EXISTING TRAINED WEIGHTS UNCHANGED")
print("PYTHON SYNTAX: PASS")
print("BACKUP:", backup)
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
