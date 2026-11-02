python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")

for f in sorted(p.glob("*.py")):
    if not any(x in f.name for x in ("adapter", "scheduler", "worker", "pipeline")):
        continue

    lines = f.read_text(errors="replace").splitlines()
    terms = (
        "predict(", "predict_batch(", "adapter.",
        "load_model", "pipeline.", "infer(",
        "mock", "stub", "placeholder",
        "return result", "return results",
        "run_inference"
    )

    hits = [i for i, s in enumerate(lines) if any(t in s.lower() for t in terms)]
    if hits:
        print(f"\n=== {f.name} ===")
        shown = set()
        for i in hits[:18]:
            for j in range(max(0, i-3), min(len(lines), i+6)):
                if j not in shown:
                    print(f"{j+1}: {lines[j][:180]}")
                    shown.add(j)
PY
