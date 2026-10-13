python - <<'PY'
from pathlib import Path
import ast
import re

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_real_sanity_verified_wiring_trial.py"
dst = base / "run_real_sanity_first_bad_fusion_input.py"

if not src.is_file():
    raise SystemExit(f"STOP: Missing existing runner: {src}")

source = src.read_text()

pattern = re.compile(
    r'(?m)^([ \t]*)print\("WORKING SOURCE AND WEIGHTS UNCHANGED", flush=True\)'
)
matches = list(pattern.finditer(source))

if len(matches) != 1:
    raise SystemExit("STOP: Fusion diagnostic insertion point not unique")

indent = matches[0].group(1)

extra = """
import numpy as np
print("\\n=== FIRST INCORRECT FUSION INPUT ===", flush=True)

names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

pt = np.asarray(stages["stacked"], dtype=np.float64)
mx = np.asarray(outputs[9].to_numpy(), dtype=np.float64)

assert pt.shape == mx.shape == (1, 8, 256)

for i, name in enumerate(names):
    live = np.asarray(
        outputs[i + 1].to_numpy(), dtype=np.float64
    ).reshape(-1)

    assert live.size == 256

    model_diff = float(
        np.max(np.abs(live - pt[0, i]))
    )
    wiring_diff = float(
        np.max(np.abs(live - mx[0, i]))
    )

    print(
        f"{name:9s} "
        f"PYTORCH_DIFF={model_diff:.9g} "
        f"WIRING_DIFF={wiring_diff:.9g}",
        flush=True
    )

print("ORIGINAL CODE AND WEIGHTS UNCHANGED", flush=True)
"""

insertion = "\n".join(
    indent + line if line else ""
    for line in extra.strip().splitlines()
) + "\n"

updated = (
    source[:matches[0].start()]
    + insertion
    + source[matches[0].start():]
)

ast.parse(updated, filename=str(dst))

if dst.exists() and dst.read_text() != updated:
    raise SystemExit("STOP: Existing diagnostic differs; not overwriting")

if not dst.exists():
    dst.write_text(updated)

print("CORRECT IMPORT CONTEXT READY")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_first_bad_fusion_input.py
