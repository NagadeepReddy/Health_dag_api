python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

base = Path("artifacts/v1.168-max/cta_max")

files = [
    base / "grecbase_fusion_order_correct_max.py",
    base / "grecbase_fusion_order_correct_max_branch_diag.py",
]

pattern = re.compile(
    r'''(?m)^([ \t]*)seq_b\s*=\s*np\.load\(
    WDIR\s*/\s*["']seq_dense\.bias\.npy["']
    \)\.astype\(np\.float32\)[ \t]*$''',
    re.VERBOSE,
)

marker = "CHECKPOINT_SEQ_DENSE_BIAS"
prepared = []

for p in files:
    if not p.is_file():
        raise SystemExit(f"STOP: Missing existing file: {p}")

    source = p.read_text()

    if marker in source:
        print("ALREADY CORRECTED:", p.name)
        continue

    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            f"STOP: Expected seq_dense.bias assignment not found "
            f"exactly once in {p.name}. Nothing changed."
        )

    indent = matches[0].group(1)

    replacement = (
        indent + "# CHECKPOINT_SEQ_DENSE_BIAS: original trained value\n"
        + indent
        + 'seq_b = __import__("torch").load('
        '"artifacts/v1.168/core-artifact/model_0_base.pt", '
        'map_location="cpu", weights_only=True)'
        '["sequence_transformer.seq_dense.bias"]'
        '.detach().cpu().numpy().astype(np.float32)'
    )

    updated = pattern.sub(lambda _: replacement, source, count=1)
    ast.parse(updated, filename=str(p))
    prepared.append((p, updated))

# Apply only after both source files pass validation.
for p, updated in prepared:
    backup = p.with_suffix(".py.before_checkpoint_seq_bias")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("CORRECTED:", p.name)
    print("BACKUP:", backup)

print("ORIGINAL PYTORCH/DS FILES UNCHANGED")
print("READY FOR CURRENT EIGHT-BRANCH VALIDATION")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
