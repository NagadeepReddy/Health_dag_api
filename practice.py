python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_parity.py")
s = p.read_text()

marker = 'pt_out = np.load(BASE + "/transformer_pytorch_output.npy")'

# Find the actual block output save instead, so we insert hooks before execution.
for candidate in [
    'pt_out = block(',
    'pt_out = model(',
]:
    if candidate in s:
        print("FOUND EXECUTION:", candidate)
        break
else:
    # Show only executable lines around the existing output save/reference.
    lines = s.splitlines()
    for i, line in enumerate(lines, 1):
        if "transformer_pytorch_output.npy" in line or "block(" in line or ".ptransformer[" in line:
            print(f"{i}: {line}")
PY
