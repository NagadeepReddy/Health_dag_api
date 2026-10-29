cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
src = dev / "run_distinct_batch2_live_max_inference.py"
dst = dev / "real_max_batch2_backend.py"

assert src.is_file(), f"STOP: Missing {src}"

original = src.read_text()
tree = ast.parse(original)
fn = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "infer_max_live"
)

assert [a.arg for a in fn.args.args] == ["model_in"]
assert not dst.exists(), f"STOP: Already exists: {dst}"

second_path = next(
    n for n in fn.body
    if isinstance(n, ast.Assign)
    and any(
        isinstance(t, ast.Name) and t.id == "second_path"
        for t in n.targets
    )
)

second_arrays = next(
    n for n in fn.body
    if isinstance(n, ast.Assign)
    and any(
        isinstance(t, ast.Tuple)
        and [x.id for x in t.elts] == ["labels2", "arrays2"]
        for t in n.targets
        if isinstance(t, ast.Tuple)
        and all(isinstance(x, ast.Name) for x in t.elts)
    )
)

assert second_path.lineno < second_arrays.lineno
assert "CTA_SECOND_MODEL_INPUT" in original
assert "build_real_inputs(model_in=second_model_in)" in original

lines = original.splitlines(keepends=True)

remove = set(range(second_path.lineno, second_arrays.lineno))

for n in ast.walk(fn):
    if isinstance(n, ast.Assert):
        segment = ast.get_source_segment(original, n) or ""
        if "different" in segment and "Inputs are identical" in segment:
            remove.update(range(n.lineno, n.end_lineno + 1))

result = []
for i, line in enumerate(lines, 1):
    if i in remove:
        continue

    if i == fn.lineno:
        assert line.strip() == "def infer_max_live(model_in):"
        line = line.replace(
            "def infer_max_live(model_in):",
            "def infer_max_batch(model_in, second_model_in):"
        )

    result.append(line)

updated = "".join(result)
parsed = ast.parse(updated)

new_fn = next(
    n for n in parsed.body
    if isinstance(n, ast.FunctionDef) and n.name == "infer_max_batch"
)

assert [a.arg for a in new_fn.args.args] == [
    "model_in", "second_model_in"
]
assert "model.execute(*runtime_inputs)" in updated
assert "pack_two_requests(arrays, arrays2)" in updated

dst.write_text(updated)

print("REAL MAX BATCH-2 BACKEND: CREATED")
print("INTERFACE: infer_max_batch(model_in, second_model_in)")
print("TWO IN-MEMORY INPUTS: SUPPORTED IN CODE")
print("ONE MAX MODEL.EXECUTE: PRESERVED")
print("DUPLICATE INPUTS: ALLOWED")
print("PYTHON SYNTAX: PASS")
print("FILE:", dst)
print("REAL RUNTIME VALIDATION: PENDING")
print("ORIGINAL RUNNER: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
