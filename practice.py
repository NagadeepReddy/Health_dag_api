python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

anchor = '    print("FINITE:", bool(np.isfinite(result).all()))'
marker = "=== REAL PYTORCH VS MAX 2048 PARITY ==="

addition = '''
    if result.shape == (1, 2048):
        print("\\n=== REAL PYTORCH VS MAX 2048 PARITY ===")
        ref_path = BASE / "real_sanity_pytorch_output.npy"
        if not ref_path.is_file():
            raise RuntimeError(f"Original PyTorch reference missing: {ref_path}")

        ref = np.load(ref_path, allow_pickle=False).astype(np.float32)
        if ref.shape != result.shape:
            raise RuntimeError(
                f"Model output shape mismatch: PT {ref.shape}, MAX {result.shape}"
            )

        diff = np.abs(result.astype(np.float64) - ref.astype(np.float64))
        print("PYTORCH MODEL SHAPE:", ref.shape)
        print("MAX MODEL SHAPE:", result.shape)
        print("MAX DIFFERENCE:", float(diff.max()))
        print("MEAN DIFFERENCE:", float(diff.mean()))
        print("NUMERICAL MATCH:", bool(np.allclose(
            result, ref, rtol=1e-3, atol=1e-3
        )))

        saved = BASE / "real_sanity_max_2048_full_runner.npy"
        if not saved.exists():
            np.save(saved, result)
            print("NEW MAX OUTPUT SAVED:", saved)
        else:
            print("EXISTING OUTPUT PRESERVED:", saved)
'''

if marker in s:
    print("REAL MODEL OUTPUT COMPARISON ALREADY PRESENT")
elif s.count(anchor) == 1:
    updated = s.replace(anchor, anchor + "\n" + addition, 1)
    ast.parse(updated, filename=str(p))
    backup = p.with_suffix(".py.before_real_2048_parity")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("REAL 2048 MODEL PARITY COMPARISON ADDED")
else:
    raise SystemExit("STOP: Expected runner line not found; nothing changed")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
