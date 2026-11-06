
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")

if not root.is_dir():
    raise SystemExit("STOP: Packaged handoff missing")

files = sorted(p for p in root.rglob("*") if p.is_file())
size = sum(p.stat().st_size for p in files)

print("=== FINAL PZAAS HANDOFF AUDIT ===")
print("TOTAL FILES:", len(files))
print("TOTAL SIZE GiB:", round(size / 1024**3, 2))

print("\n=== COMPONENT SIZES ===")

for name in ("model", "runtime", "config", "docs"):
    folder = root / name
    subset = [p for p in files if folder in p.parents]
    total = sum(p.stat().st_size for p in subset)
    print(f"{name}: {len(subset)} files, {total / 1048576:.1f} MiB")

print("\n=== LARGEST FILES ===")

for path in sorted(
    files, key=lambda p: p.stat().st_size, reverse=True
)[:12]:
    print(
        f"{path.stat().st_size / 1048576:.1f} MiB",
        path.relative_to(root)
    )

print("\n=== POSSIBLE UNNECESSARY FILES ===")

suspect = []
for path in files:
    rel = path.relative_to(root)
    parts = [part.lower() for part in rel.parts]
    name = path.name.lower()

    if (
        any(part in {
            "__pycache__", ".pytest_cache", "tests",
            "test", "benchmarks", ".git"
        } for part in parts[:-1])
        or name.startswith("test_")
        or name.endswith((
            ".pyc", ".pyo", ".log", ".bak",
            ".tmp", ".whl", ".before_pack72"
        ))
    ):
        suspect.append(path)

print("CLEANUP CANDIDATES:", len(suspect))

for path in suspect[:20]:
    print("REVIEW:", path.relative_to(root))

if len(suspect) > 20:
    print("ADDITIONAL CANDIDATES:", len(suspect) - 20)

print("\n=== CONTENT DUPLICATES (1 MiB OR LARGER) ===")

by_size = defaultdict(list)

for path in files:
    n = path.stat().st_size
    if n >= 1048576:
        by_size[n].append(path)

duplicates = []
for group in by_size.values():
    if len(group) < 2:
        continue

    by_hash = defaultdict(list)

    for path in group:
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(
                lambda: stream.read(1024 * 1024), b""
            ):
                h.update(chunk)
        by_hash[h.hexdigest()].append(path)

    for identical in by_hash.values():
        if len(identical) > 1:
            duplicates.append(identical)

savings = sum(
    (len(group) - 1) * group[0].stat().st_size
    for group in duplicates
)

print("DUPLICATE GROUPS:", len(duplicates))
print("POTENTIAL SAVINGS MiB:", round(savings / 1048576, 1))

for group in duplicates[:8]:
    print("DUPLICATE GROUP:")
    for path in group[:5]:
        print(" ", path.relative_to(root))

print("\n=== SHARED LAUNCHER CHECK ===")

launcher = root / "runtime/launch_max_model.sh"
config = root / "config/model.env"

if not launcher.is_file() or not config.is_file():
    raise SystemExit("STOP: Shared launcher/config missing")

launcher_text = launcher.read_text()
config_text = config.read_text()

print(
    "MODEL-INDEPENDENT LAUNCHER SOURCE:",
    not any(
        name in launcher_text.lower()
        for name in ("cta", "bplan", "pzaas")
    )
)
print(
    "MODEL CONFIG SEPARATED:",
    "MODULE=" in config_text
    and "MODEL_PYTHONPATH=" in config_text
)
print(
    "VM-SPECIFIC PODMAN DEFAULT:",
    "/application1/podman/storage" in launcher_text
)

print("\n=== AUDIT COMPLETE ===")
print("PACKAGED COLD START: PREVIOUSLY PASSED")
print("NO FILES MODIFIED OR DELETED")
PY
