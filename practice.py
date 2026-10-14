cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
from textwrap import indent
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_real_sanity_full_head_72.py"
dst = base / "run_live_max_inference.py"

assert not dst.exists(), "STOP: Live runner already exists"

lines = src.read_text().splitlines(keepends=True)

starts = [
    i for i, line in enumerate(lines)
    if line.strip() == "labels, arrays = build_real_inputs()"
]
ends = [
    i for i, line in enumerate(lines)
    if line.strip() == "for i, output in enumerate(outputs):"
]

assert len(starts) == len(ends) == 1, "STOP: Runner structure differs"

start, end = starts[0], ends[0]
assert start < end

body = "".join(lines[start:end])
assert "session.load(" in body
assert "model.execute(*runtime_inputs)" in body

body = body.replace(
    "labels, arrays = build_real_inputs()",
    "labels, arrays = build_real_inputs(model_in=model_in)",
    1
)

new_code = (
    "".join(lines[:start])
    + "\ndef infer_max_live(model_in):\n"
    + indent(body, "    ")
    + """
    results = [
        np.asarray(o.to_numpy(), dtype=np.float32)
        for o in outputs
    ]
    assert len(results) == 1, "Unexpected MAX output count"
    assert np.isfinite(results[0]).all(), "Non-finite MAX output"
    return results[0]
"""
)

ast.parse(new_code)
dst.write_text(new_code)

print("LIVE MAX RUNNER: CREATED")
print("EXISTING GRAPH AND WEIGHTS: REUSED")
print("LIVE 72-INPUT ADAPTER: CONNECTED")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL RUNNER/DS/PIPELINE: UNCHANGED")
print("LIVE EXECUTION: NOT YET TESTED")
PY
