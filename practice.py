python3 - <<'PY'
from pathlib import Path
import re
import py_compile

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/bplan_batch2_graph_dev")
src = root / "grecbase_fusion_full_head_72_batch2.py"
dst = root / "grecbase_fusion_full_head_72_batch2_v2.py"

if not src.is_file():
    raise SystemExit(f"STOP: Source missing: {src}")

if dst.exists():
    raise SystemExit(f"STOP: Candidate already exists: {dst}")

code = src.read_text()

# Convert graph input batch dimensions only.
code, inputs = re.subn(
    r'(TensorType\(DType\.\w+,\s*\[)\s*1(?=\s*,)',
    r'\g<1>2',
    code
)

if inputs < 2:
    raise SystemExit(f"STOP: Unexpected graph input structure: {inputs} changes")

# Convert explicit batch-dependent reshapes.
code, reshapes = re.subn(
    r'(ops\.reshape\(\s*(?:x|outs|value|remaining\[66\])\s*,\s*\[)\s*1(?=\s*,)',
    r'\g<1>2',
    code
)

compile(code, str(dst), "exec")
dst.write_text(code)
py_compile.compile(str(dst), cfile="/tmp/bplan_batch2_v2.pyc", doraise=True)

print("BPLAN BATCH-2 CANDIDATE: CREATED")
print("FILE:", dst)
print("GRAPH INPUT CHANGES:", inputs)
print("RESHAPE CHANGES:", reshapes)
print("PYTHON SYNTAX: PASS")
print("ORIGINAL SOURCE: UNCHANGED")
print("MAX GRAPH COMPILATION: PENDING")
print("REAL BATCH-2 INFERENCE: PENDING")
PY
