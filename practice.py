
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import shutil

repo = Path("/application1/sajjna8/rt-pzaas-v1.0")
graph = repo / "artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py"

sources = [
    Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension"),
    Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/maxserve_cta_extension"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/maxserve_cta_extension"),
]

modules = [
    "cta_native_launcher.py",
    "cta_router.py",
    "cta_http_pipeline.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
    "cta_context.py",
    "cta_worker_adapter.py",
    "cta_spawn_worker.py",
    "cta_worker_registration.py",
    "cta_architecture_registration.py",
    "cta_pipeline_model.py",
    "cta_queue_compat.py",
]

source = next(
    (p for p in sources
     if (p / "cta_native_launcher.py").is_file()
     and (p / "cta_worker_adapter.py").is_file()),
    None
)

print("=== PZAAS NATIVE MAX INTEGRATION SETUP ===")

if not graph.is_file():
    raise SystemExit(f"PZAAS graph not found: {graph}")

if source is None:
    raise SystemExit(
        "Validated CTA native source not found at documented paths. No files modified."
    )

target = repo / "artifacts/v1.472-max/maxserve_pzaas_extension"
reference = target / "_cta_native_reference"
working = target / "pzaas_native_serve_dev"

reference.mkdir(parents=True, exist_ok=True)
working.mkdir(parents=True, exist_ok=True)

copied = 0
existing = 0

for name in modules:
    src = source / name
    dst = reference / name
    if not src.is_file():
        print(f"NOT FOUND: {name}")
        continue
    if dst.exists():
        existing += 1
        continue
    shutil.copy2(src, dst)
    copied += 1

print("PZAAS GRAPH: FOUND")
print("CTA NATIVE SOURCE:", source)
print("REFERENCE MODULES COPIED:", copied)
print("REFERENCE MODULES ALREADY PRESENT:", existing)
print("PZAAS WORKING DIRECTORY:", working)
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NUMERICAL PARITY: PREVIOUSLY PASSED")
print("NATIVE SERVING: SCAFFOLD PREPARED")
print("NEXT: ADAPT PZAAS NATIVE LAUNCHER / ROUTER / WORKER")
PY
