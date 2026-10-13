python - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")

for label, prefix, filename in [
    ("SIBLING", "sibling_context_head", "sibling_context_max.py"),
    ("CONTEXT", "context_head", "main_context_max.py"),
]:
    print("\n===", label, "BATCHNORM CHECK ===")

    paths = {}
    for name in ("weight", "bias", "running_mean", "running_var"):
        matches = list(base.rglob(
            prefix + ".num_batch_norm." + name + ".npy"
        ))
        print(name, "files:", len(matches))
        if len(matches) == 1:
            paths[name] = matches[0]

    source = base / filename
    if source.exists():
        lines = source.read_text().splitlines()
        for i, line in enumerate(lines):
            if ".num_batch_norm." in line:
                print(f"MAX LINE {i+1}: {line.strip()}")

    if len(paths) == 4:
        gamma = np.load(paths["weight"]).astype(np.float64)
        beta = np.load(paths["bias"]).astype(np.float64)
        mean = np.load(paths["running_mean"]).astype(np.float64)
        var = np.load(paths["running_var"]).astype(np.float64)

        print("FEATURES:", gamma.shape)
        print("MAX ABS RUNNING MEAN:", float(np.max(np.abs(mean))))
        print("RUNNING VAR RANGE:", float(var.min()), float(var.max()))

        # Quantify the difference for actual -1 / 0 feature values.
        for value in (-1.0, 0.0):
            current = value * gamma + beta
            correct = (
                (value - mean) / np.sqrt(var + 1e-5)
            ) * gamma + beta
            print(
                "INPUT:", value,
                "MAX FORMULA DIFFERENCE:",
                float(np.max(np.abs(current - correct)))
            )
    else:
        print("Complete BatchNorm statistics not found.")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
