podman run --rm -i --entrypoint python \
  -v "$PWD:/workspace:Z" -w /workspace \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, runpy, io, contextlib
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max").resolve()
sys.path[:0] = [str(base), str(base.parent)]

print("Running current MAX graph...", flush=True)

with contextlib.redirect_stdout(io.StringIO()):
    result = runpy.run_path(
        str(base / "run_real_sanity_max_branch_diag.py"),
        run_name="__main__"
    )

outputs = result["outputs"]
assert len(outputs) == 9, len(outputs)

final = np.asarray(outputs[0].to_numpy()).reshape(1, 2048)
names = [
    "sequence", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

branches = [
    np.asarray(out.to_numpy()).reshape(1, 256)
    for out in outputs[1:]
]

combined = np.concatenate(branches, axis=1)
diff = np.abs(final.astype(np.float64) -
              combined.astype(np.float64))

print("\n=== CURRENT FINAL OUTPUT ASSEMBLY ===")
print("FINAL SHAPE:", final.shape)
print("COMBINED SHAPE:", combined.shape)
print("MAX_DIFF:", float(diff.max()))
print("MEAN_DIFF:", float(diff.mean()))
print("RAW CONCAT MATCH:", bool(np.allclose(
    final, combined, rtol=1e-3, atol=1e-3
)))

for i, name in enumerate(names):
    part = final[:, i*256:(i+1)*256]
    d = np.abs(part.astype(np.float64) -
               branches[i].astype(np.float64))
    print(name, "FINAL SEGMENT MAX_DIFF:", float(d.max()))
PY
