podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
from pathlib import Path
import ast
import re
import sys

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "run_real_sanity_verified_wiring_trial.py"
)
source = p.read_text()

pattern = re.compile(
    r'(?m)^([ \t]*)print\("WORKING SOURCE AND WEIGHTS UNCHANGED", flush=True\)'
)
matches = list(pattern.finditer(source))
if len(matches) != 1:
    raise SystemExit("STOP: Existing fusion trial differs from verified version")

indent = matches[0].group(1)

extra = '''
print("\\n=== FIRST ACTUAL FUSION MISMATCH ===", flush=True)
names = ["sequence", "context", "search0", "search1",
         "task", "jet", "ihq", "sibling"]

pt = np.asarray(stages["stacked"], dtype=np.float64)
mx = np.asarray(outputs[9].to_numpy(), dtype=np.float64)

assert pt.shape == mx.shape == (1, 8, 256)

for i, name in enumerate(names):
    branch = np.asarray(
        outputs[i + 1].to_numpy(), dtype=np.float64
    ).reshape(-1)
    actual = mx[0, i].reshape(-1)
    expected = pt[0, i].reshape(-1)

    assert branch.size == actual.size == expected.size == 256

    branch_diff = float(np.max(np.abs(branch - expected)))
    wiring_diff = float(np.max(np.abs(branch - actual)))

    print(
        f"{name:9s} "
        f"PYTORCH_DIFF={branch_diff:.9g} "
        f"WIRING_DIFF={wiring_diff:.9g} "
        f"{'PASS' if branch_diff < 1e-3 and wiring_diff < 1e-5 else 'FAIL'}",
        flush=True
    )

print("ORIGINAL FILES UNCHANGED", flush=True)
'''

insertion = "\n".join(
    indent + line if line else ""
    for line in extra.strip().splitlines()
) + "\n"

source = (
    source[:matches[0].start()]
    + insertion
    + source[matches[0].start():]
)

ast.parse(source)
sys.path.insert(0, str(p.parent.parent))
exec(
    compile(source, str(p), "exec"),
    {"__name__": "__main__", "__file__": str(p)}
)
PY
