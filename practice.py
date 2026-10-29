cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

roots = [
    Path("/application1/cta_max_native_release_candidate_20261028"),
    Path("artifacts/v1.168-max/maxserve_cta_extension"),
]

names = (
    "cta_native_launcher.py",
    "cta_spawn_worker.py",
    "cta_scheduler_factory.py",
)

for root in roots:
    print("\n=== SOURCE:", root, "===")
    for name in names:
        p = root / name
        if not p.is_file():
            continue
        print("\nFILE:", p)
        lines = p.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            if any(x in line.lower() for x in (
                "launch", "main(", "serve", "worker",
                "factory", "model_path", "model_id",
                "host", "port", "architecture",
                "if __name__"
            )):
                lo, hi = max(0, i-2), min(len(lines), i+3)
                for j in range(lo, hi):
                    print(f"{j+1}: {lines[j][:170]}")

print("\nLIVE MAX STARTUP REVIEW COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTED: NO")
PY
