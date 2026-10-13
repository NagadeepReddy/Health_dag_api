cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python3 - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
lines = p.read_text().splitlines(keepends=True)

starts = [i for i, x in enumerate(lines)
          if x.strip() == "seq_raw = postprocess(sx2)"]
ends = [i for i, x in enumerate(lines)
        if x.strip().startswith("seq = ops.matmul(seq_raw,")]

assert len(starts) == len(ends) == 1, "STOP: unexpected source"
a, b = starts[0], ends[0]
assert a < b and b-a <= 10, "STOP: unexpected block"

block = "".join(lines[a:b+1])
for token in ("seq_w = np.load", "seq_b = np.load",
              "assert seq_w.shape", "assert seq_b.shape"):
    assert token in block, f"STOP: missing {token}"

backup = p.with_name(p.name + ".before_duplicate_seq_dense_fix")
assert not backup.exists(), "STOP: backup already exists"
shutil.copy2(p, backup)

indent = lines[a][:len(lines[a])-len(lines[a].lstrip())]
lines[a:b+1] = [indent + "seq = postprocess(sx2)\n"]
p.write_text("".join(lines))

print("FIX APPLIED: Removed duplicate seq_dense")
print("BACKUP:", backup)
PY

python3 -m py_compile \
  artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
