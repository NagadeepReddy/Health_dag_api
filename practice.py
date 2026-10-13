cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python3 - <<'PY'
from pathlib import Path
import ast, shutil

b = Path("artifacts/v1.168-max/cta_max")
p = b / "run_real_sanity_full_head_72.py"
s = p.read_text()
lines = s.splitlines(keepends=True)

starts = [i for i, x in enumerate(lines)
          if x.strip() == "if result.shape == (1, 2048):"]
ends = [i for i, x in enumerate(lines)
        if x.strip() == "if result.shape == (1, 10819):"]

assert len(starts) == len(ends) == 1, "STOP: Unexpected runner"
a, z = starts[0], ends[0]
assert a < z, "STOP: Invalid code boundaries"
assert "HEAD VS FUSION MAX DIFF" in "".join(lines[a:z]), \
    "STOP: Existing validation changed"

replacement = '''
    if result.shape == (1, 2048):
        import torch
        import torch.nn.functional as F

        weights = BASE / "get_path_weights"

        def wt(name):
            return torch.from_numpy(
                np.load(weights / (name + ".npy")).astype(np.float32)
            )

        fusion_ref = np.load(
            BASE / "real_sanity_pytorch_same_input_verified.npz"
        )["final"].astype(np.float32)

        with torch.no_grad():
            x = torch.from_numpy(fusion_ref)
            x = F.linear(x, wt("remove_tasks_dense1.weight"),
                         wt("remove_tasks_dense1.bias"))
            a = F.linear(x, wt("remove_tasks_act1.w1.weight"))
            c = F.linear(x, wt("remove_tasks_act1.w3.weight"))
            expected = F.linear(
                F.silu(a) * c,
                wt("remove_tasks_act1.w2.weight")
            ).numpy()

        assert result.shape == expected.shape == (1, 2048)

        diff = np.abs(result - expected)
        passed = bool(np.allclose(
            result, expected, rtol=1e-3, atol=1e-3
        ))

        print("INTEGRATED MAX HEAD MAX DIFF:", float(diff.max()))
        print("INTEGRATED MAX HEAD MEAN DIFF:", float(diff.mean()))
        print("INTEGRATED HEAD PARITY:", passed)

        if passed:
            saved = BASE / "real_sanity_integrated_head_72_verified.npy"
            np.save(saved, result)
            print("INTEGRATED OUTPUT SAVED:", saved)
        else:
            print("STOP: Integrated graph parity not yet established")

'''

updated = "".join(lines[:a]) + replacement + "".join(lines[z:])
ast.parse(updated)

backup = p.with_name(p.name + ".before_integrated_head_parity")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("INTEGRATED PARITY CHECK READY")
print("ORIGINAL DS AND PIPELINE UNCHANGED")
print("PYTHON SYNTAX PASS")
PY

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_full_head_72.py
