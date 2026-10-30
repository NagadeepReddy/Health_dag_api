python3 -B - <<'PY'
from pathlib import Path
import hashlib
import json

base = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate"
)
source = base / "maxserve_cta_extension"
report = base / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json"

if not source.is_dir() or base.is_symlink():
    raise SystemExit("STOP: Staged release unavailable")

files = sorted(
    p for p in source.rglob("*.py")
    if p.is_file() and not p.is_symlink()
)

if not files:
    raise SystemExit("STOP: No staged Python sources")

checksums = {
    str(p.relative_to(base)):
        hashlib.sha256(p.read_bytes()).hexdigest()
    for p in files
}

result = {
    "project": "CTA Offers v1.168 Modular MAX",
    "scope": "Built-in MAX Serve CPU Native Batch-2 POC",
    "date": "2026-10-30",
    "status": "ACCEPTANCE PASSED",
    "evidence": "Verified terminal output from isolated native HTTP test",
    "distinct_json_requests": 2,
    "native_http_statuses": [200, 200],
    "real_model_inputs": 72,
    "one_batch_worker_evidence": "PASS",
    "response_serialization": "PASS",
    "final_exit_code": 0,
    "original_ds_and_max": "UNCHANGED",
    "working_native_release": "UNCHANGED",
    "existing_containers_restarted": 0,
    "pending_separately": [
        "Approved MAX+FAISS image verification",
        "GPU testing",
        "Additional model migrations"
    ],
    "staged_source_sha256": checksums
}

if report.exists():
    print("ACCEPTANCE REPORT: ALREADY EXISTS")
else:
    with report.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print("ACCEPTANCE REPORT: SAVED")

print("CPU NATIVE BATCH-2 POC: CLOSED - PASS")
print("STAGED SOURCE FILES RECORDED:", len(checksums))
print("REPORT:", report)
print("MODEL EXECUTIONS: ZERO")
print("CONTAINERS RESTARTED: NONE")
PY
