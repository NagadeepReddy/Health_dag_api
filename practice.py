python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for name in [
    "grecbase_get_path_max.py",
    "grecbase_fusion_all8_max.py",
]:
    p = base / name
    print(f"\n=== {name} ===")
    assert p.is_file(), f"Missing: {p}"
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines):
        if any(k in line for k in (
            "remove_tasks_dense2",
            "grecbase_get_path_max(",
            "graph.output(",
            "return linear(",
            "return result",
        )):
            lo = max(0, i - 3)
            hi = min(len(lines), i + 5)
            for j in range(lo, hi):
                print(f"{j+1}: {lines[j]}")
            print("---")

print("READ ONLY — NO FILES MODIFIED")
PY
