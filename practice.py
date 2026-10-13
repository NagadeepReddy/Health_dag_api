cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python3 - <<'PY'
from pathlib import Path
import ast, shutil

base = Path("artifacts/v1.168-max/cta_max")
p = base / "run_real_sanity_full_head_72.py"
src = p.read_text()
lines = src.splitlines(keepends=True)

starts = [i for i, x in enumerate(lines)
          if x.strip() == "if result.shape == (1, 2048):"]
ends = [i for i, x in enumerate(lines)
        if x.strip() == "if result.shape == (1, 10819):"]

assert len(starts) == len(ends) == 1, "STOP: Unexpected runner"
a, b = starts[0], ends[0]
assert a < b, "STOP: Invalid boundaries"
assert "real_sanity_pytorch_same_input_verified.npz" in "".join(lines[a:b]), \
    "STOP: Reference block differs"

replacement = '''
    if result.shape == (1, 2048):
        fusion = np.load(
            BASE / "real_sanity_pytorch_same_input_verified.npz"
        )["final"].astype(np.float32)

        assert fusion.shape == result.shape

        diff = np.abs(result - fusion)

        print("FINAL HEAD OUTPUT SHAPE:", result.shape)
        print("HEAD VS FUSION MAX DIFF:", float(diff.max()))

        saved = BASE / "real_sanity_max_get_path_2048_latest.npy"
        np.save(saved, result)
        print("FINAL HEAD OUTPUT SAVED:", saved)

        if float(diff.max()) < 1e-3:
            print("WARNING: Output still resembles fusion; verify head execution")
        else:
            print("HEAD OUTPUT DIFFERS FROM FUSION")

'''

updated = "".join(lines[:a]) + replacement + "".join(lines[b:])
ast.parse(updated)

backup = p.with_name(p.name + ".before_head_validation_fix")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("FINAL HEAD VALIDATION UPDATED")
print("ORIGINAL MAX GRAPH UNCHANGED")
print("SYNTAX PASS")
PY

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_full_head_72.py
