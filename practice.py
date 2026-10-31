python3 -B - <<'PY'
from pathlib import Path
import ast
import struct

roots = [
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1"),
    Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
]

for root in roots:
    print("\n===", root, "===")
    if not root.is_dir():
        continue
    for name in ("seq_dense.weight.npy", "seq_dense_weight.npy"):
        for p in root.rglob(name):
            try:
                with p.open("rb") as f:
                    assert f.read(6) == b"\x93NUMPY"
                    major, minor = f.read(2)
                    length = struct.unpack(
                        "<H" if major == 1 else "<I",
                        f.read(2 if major == 1 else 4)
                    )[0]
                    header = ast.literal_eval(f.read(length).decode("latin1"))
                print("SHAPE:", header["shape"], "|", p)
            except Exception as e:
                print("ERROR:", p, str(e))
PY
