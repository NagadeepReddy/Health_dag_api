python - <<'PY'
from pathlib import Path
import ast
import re
import textwrap

base = Path("artifacts/v1.168-max/cta_max")
source = base / "run_real_sanity_fusion_stage_trial.py"
trial = base / "run_real_sanity_fusion_slot_alignment.py"

if not source.is_file():
    raise SystemExit("STOP: Existing fusion-stage runner missing")

code = source.read_text()
pattern = re.compile(
    r'(?m)^([ \t]*)print\("WORKING SOURCE AND WEIGHTS UNCHANGED", flush=True\)[ \t]*$'
)
matches = list(pattern.finditer(code))

if len(matches) != 1:
    raise SystemExit("STOP: Stage diagnostic insertion point not unique")

extra = """
print("\\n=== EXACT FUSION STACK ROOT CAUSE ===", flush=True)
from itertools import permutations

names = (
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
)

pt_stack = np.asarray(stages["stacked"], dtype=np.float64)
mx_stack = np.asarray(outputs[9].to_numpy(), dtype=np.float64)

assert pt_stack.shape == mx_stack.shape == (1, 8, 256), (
    pt_stack.shape, mx_stack.shape
)

cost = np.array([
    [
        np.max(np.abs(pt_stack[0, i] - mx_stack[0, j]))
        for j in range(8)
    ]
    for i in range(8)
])

print("\\nPYTORCH BRANCH -> CLOSEST MAX STACK SLOT")
for i, name in enumerate(names):
    nearest = int(np.argmin(cost[i]))
    print(
        f"{name:9s} expected_slot={i} "
        f"closest_max_slot={nearest} "
        f"closest_diff={cost[i, nearest]:.9g} "
        f"same_slot_diff={cost[i, i]:.9g}"
    )

best = min(
    permutations(range(8)),
    key=lambda p: sum(cost[i, p[i]] for i in range(8))
)

print("\\nBEST ONE-TO-ONE SLOT MAPPING:", best)
print("BEST MAPPING MAX_DIFF:",
      float(max(cost[i, best[i]] for i in range(8))))

print("\\nMAX BRANCH OUTPUT -> MAX FUSION STACK SLOT")
for j, name in enumerate(names):
    branch = np.asarray(
        outputs[j + 1].to_numpy(),
        dtype=np.float64
    ).reshape(-1)

    slot = mx_stack[0, j].reshape(-1)

    if branch.shape != slot.shape:
        print(name, "SHAPE MISMATCH",
              branch.shape, slot.shape)
    else:
        print(
            name,
            "SLOT:", j,
            "MAX_DIFF:", float(np.max(np.abs(branch - slot)))
        )

if max(cost[i, best[i]] for i in range(8)) < 1e-3:
    print("\\nCAUSE: STACK ORDER / PERMUTATION")
else:
    print("\\nCAUSE: STACK CONTENT OR WIRING; NOT JUST ORDER")

print("READ ONLY: ORIGINAL MODEL AND WEIGHTS UNCHANGED")
"""

indent = matches[0].group(1)
addition = textwrap.indent(textwrap.dedent(extra).strip(), indent)

updated = (
    code[:matches[0].start()]
    + addition + "\n"
    + code[matches[0].start():]
)

ast.parse(updated, filename=str(trial))

if trial.exists():
    if trial.read_text() != updated:
        raise SystemExit("STOP: Existing trial differs; not overwriting")
else:
    trial.write_text(updated)

print("FUSION SLOT DIAGNOSTIC READY")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_fusion_slot_alignment.py
