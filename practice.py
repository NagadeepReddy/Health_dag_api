
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

repo = Path.cwd()
base = repo / "artifacts/v1.472-max"
ext = base / "maxserve_pzaas_extension"
native = ext / "pzaas_native_serve_dev"
graph = base / "pzaas_max"
original = repo / "artifacts/v1.472"
shared = Path("/application1/max_shared_python_deps")

print("=== PZAAS CLEAN RELEASE INVENTORY ===")

for path in (native, graph, original):
    if not path.is_dir():
        raise SystemExit(f"STOP: Required folder missing: {path}")

print("\n=== NATIVE SERVING FILES ===")
native_files = sorted(native.glob("*.py"))

for path in native_files:
    print(
        f"{path.name:48} "
        f"{path.stat().st_size:,} bytes"
    )

print("\n=== MAX GRAPH / MODEL COMPONENTS ===")
for path in sorted(graph.glob("*.py")):
    print(path.relative_to(base))

print("\n=== DIRECT RUNTIME IMPORTS ===")

entry_names = (
    "pzaas_native_launcher.py",
    "pzaas_spawn_worker.py",
    "pzaas_max_model_adapter.py",
    "pzaas_worker_adapter.py",
    "pzaas_live_pack_72.py",
    "pzaas_http_pipeline.py",
    "pzaas_router.py",
)

for name in entry_names:
    path = native / name
    if not path.is_file():
        print(f"{name}: NOT FOUND")
        continue

    print(f"\n{name}")

    tree = ast.parse(path.read_text(), filename=str(path))

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if (
                "pzaas" in module.lower()
                or module in ("pipeline", "models", "Model")
                or module.startswith("maxserve")
            ):
                imports.add(module)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "pzaas" in alias.name.lower():
                    imports.add(alias.name)

    for item in sorted(imports):
        print("  ", item)

print("\n=== TRAINED MODEL / AUXILIARY ASSETS ===")

suffixes = {".pt", ".pth", ".bin", ".npy", ".npz",
            ".pkl", ".pickle", ".faiss", ".index"}

count = 0
for path in original.rglob("*"):
    if path.is_file() and path.suffix.lower() in suffixes:
        count += 1
        if count <= 35:
            print(
                path.relative_to(repo),
                f"({path.stat().st_size / 1048576:.1f} MiB)"
            )

print("TOTAL ORIGINAL ASSET CANDIDATES:", count)

print("\n=== POTENTIAL CLEANUP CANDIDATES ===")

for path in sorted(ext.iterdir()):
    name = path.name.lower()
    if any(part in name for part in (
        "test", "validation", "reference", "backup",
        "debug", "experiment", "evidence", "archive"
    )):
        print("REVIEW:", path.relative_to(repo))

print("\n=== CROSS-MODEL REFERENCES ===")
matches = []

for path in native_files:
    for number, line in enumerate(
        path.read_text(errors="replace").splitlines(), 1
    ):
        if any(term in line.lower() for term in (
            "cta_", "bplan", "/application1/",
            "/vzwhome/"
        )):
            matches.append(
                f"{path.name}:{number}: {line.strip()[:130]}"
            )

if matches:
    for match in matches[:35]:
        print(match)
else:
    print("No obvious CTA/BPLAN or VM absolute-path references")

print("\n=== SHARED DEPENDENCY LOCATION ===")
print("EXISTS:", shared.is_dir())
print("PATH:", shared)

print("\n=== CURRENT POC ARCHIVE ===")
archives = sorted(
    repo.glob("PZAAS_MAX_CPU_POC_HANDOFF_*.tar.gz")
)
for path in archives:
    print(path.name, f"({path.stat().st_size / 1048576:.1f} MiB)")

print("\n=== NEXT RELEASE REQUIREMENTS ===")
print("Model-specific runtime files: review required")
print("Shared infrastructure separation: pending")
print("Clean independent container: pending")
print("External Postman: pending")
print("Final portable handoff: pending")
print("NO FILES MODIFIED OR DELETED")
PY
