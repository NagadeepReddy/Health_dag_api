python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py")
s = p.read_text()

old = "return x.detach().cpu().numpy().astype(np.int64)"
new = "return x.detach().cpu().numpy().astype(np.float32 if x.is_floating_point() else np.int64)"

if old in s:
    s = s.replace(old, new, 1)
    s = s.replace(
        "assert all(np.issubdtype(x.dtype, np.integer) for x in inputs)",
        "assert all(x.dtype in (np.dtype('int64'), np.dtype('float32')) for x in inputs)"
    )
    ast.parse(s)
    backup = p.with_suffix(".py.before_dtype_fix")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(s)
    print("REAL INPUT DTYPE PRESERVATION FIXED")
elif new in s:
    print("INPUT DTYPE FIX ALREADY PRESENT")
else:
    raise SystemExit("STOP: Adapter changed unexpectedly")
PY

cat > artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py <<'PY'
import sys
from pathlib import Path
import numpy as np

from max.driver import CPU, Tensor
from max.graph import DeviceRef
from max.engine import InferenceSession

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from run_real_sanity_input_adapter import build_real_inputs
from grecbase_fusion_order_correct_max import (
    build_grecbase_fusion_graph_order_correct,
)

labels, arrays = build_real_inputs()

device = CPU()
device_ref = DeviceRef.from_device(device)

print("=== BUILD EXISTING CORRECTED MAX GRAPH ===", flush=True)
graph = build_grecbase_fusion_graph_order_correct(device_ref)

print("SAVED REAL INPUTS:", len(arrays))
print("MAX GRAPH INPUTS:", len(graph.inputs))

if len(graph.inputs) != len(arrays):
    raise SystemExit("STOP: Graph input count differs")

runtime_inputs = []
errors = []

for i, (label, value, graph_input) in enumerate(
    zip(labels, arrays, graph.inputs)
):
    target_type = graph_input.type
    dtype_name = str(target_type.dtype).lower()

    if "float32" in dtype_name:
        value = np.asarray(value, dtype=np.float32)
    elif "int64" in dtype_name:
        value = np.asarray(value, dtype=np.int64)
    else:
        errors.append(
            f"{i} {label}: unsupported graph dtype {dtype_name}"
        )
        continue

    try:
        expected_shape = tuple(int(d) for d in target_type.shape)
        if value.shape != expected_shape:
            errors.append(
                f"{i} {label}: real {value.shape}, "
                f"graph expects {expected_shape}"
            )
    except (ValueError, TypeError):
        print(
            f"Dynamic shape at {i} {label}: {target_type.shape}"
        )

    runtime_inputs.append(Tensor.from_numpy(value))

if errors:
    print("\n=== INPUT CONTRACT ISSUES ===")
    for error in errors:
        print(error)
    raise SystemExit(
        "STOP: Correct graph input declarations before execution"
    )

print("REAL INPUT CONTRACT: PASS", flush=True)

session = InferenceSession(devices=[device])

print("COMPILING EXISTING MAX GRAPH...", flush=True)
model = session.load(graph)

print("EXECUTING REAL CTA INPUTS...", flush=True)
outputs = model.execute(*runtime_inputs)

for i, output in enumerate(outputs):
    result = np.asarray(output)
    print("OUTPUT", i, "SHAPE:", result.shape)
    print("FINITE:", bool(np.isfinite(result).all()))

    if result.shape == (1, 10819):
        ref_path = BASE / "real_sanity_pytorch_final_from_2048_candidate.npy"
        if ref_path.exists():
            ref = np.load(ref_path)
            if ref.shape == result.shape:
                difference = np.abs(
                    result.astype(np.float64)
                    - ref.astype(np.float64)
                )
                print("CANDIDATE REFERENCE MAX DIFF:",
                      float(difference.max()))
                print("CANDIDATE REFERENCE MATCH:",
                      bool(np.allclose(
                          result, ref, rtol=1e-3, atol=1e-3
                      )))
                print(
                    "NOTE: Candidate reference must be confirmed "
                    "as the original PyTorch final output"
                )

print("FULL REAL-INPUT MAX EXECUTION COMPLETED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
