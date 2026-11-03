cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

src = Path("/application1/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")
dst = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev")

names = [
    "__init__.py",
    "bplan_architecture_registration.py",
    "bplan_context.py",
    "bplan_http_pipeline.py",
    "bplan_native_launcher.py",
    "bplan_native_scheduler.py",
    "bplan_pipeline_model.py",
    "bplan_queue_compat.py",
    "bplan_router.py",
    "bplan_scheduler_factory.py",
    "bplan_spawn_worker.py",
    "bplan_worker_registration.py",
]

missing = [n for n in names if not (src/n).is_file()]
existing = [n for n in names if (dst/n.replace("bplan", "pzaas")).exists()]

if missing or existing:
    raise SystemExit(f"STOP: missing={missing}, existing={existing}")

dst.mkdir(parents=True, exist_ok=True)

for name in names:
    text = (src/name).read_text()
    for old, new in [
        ("bplan", "pzaas"),
        ("BPlan", "PZAAS"),
        ("BPLAN", "PZAAS"),
        ("v1.113", "v1.472"),
    ]:
        text = text.replace(old, new)

    target = dst/name.replace("bplan", "pzaas")
    compile(text, str(target), "exec")
    target.write_text(text)
    print("CREATED:", target.name)

print("\nPZAAS NATIVE MAX SCAFFOLD: CREATED")
print("MODEL ADAPTER: NOT YET IMPLEMENTED")
print("RUNTIME VALIDATION: PENDING")
PY
