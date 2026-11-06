
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"

test -f "$EVIDENCE/pzaas_native_response.json" || {
  echo "STOP: Saved MAX response missing"
  exit 1
}

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/workspace:ro" \
  -v "$EVIDENCE:/evidence:rw" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import ast
import importlib
import json
import os
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

os.umask(0o077)

root = Path(
    "/workspace/artifacts/v1.472-max/"
    "maxserve_pzaas_extension/pzaas_native_serve_dev"
)
spawn = root / "pzaas_spawn_worker.py"
fixture = root / "pzaas_adjusted_sanity_input.json"
reference = Path("/evidence/pzaas_native_response.json")
log = Path("/evidence/pzaas_original_baseline.log")

for path in (spawn, fixture, reference):
    if not path.is_file():
        raise SystemExit(f"STOP: Missing {path}")

tree = ast.parse(spawn.read_text())

# Recover the original pipeline class from the verified
# PZAAS worker source rather than assuming an import name.
imports = [
    (node.module, alias.name)
    for node in ast.walk(tree)
    if isinstance(node, ast.ImportFrom)
    for alias in node.names
    if alias.asname == "PZAASPipeline"
       or alias.name == "PZAASPipeline"
]

if len(set(imports)) != 1:
    raise SystemExit(
        f"STOP: Cannot uniquely locate PZAASPipeline import: {imports}"
    )

# Apply literal environment defaults from the native
# worker, without executing or importing its MAX hook.
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    if not (
        isinstance(func, ast.Attribute)
        and func.attr == "setdefault"
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "environ"
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == "os"
        and len(node.args) >= 2
        and all(
            isinstance(x, ast.Constant) and isinstance(x.value, str)
            for x in node.args[:2]
        )
    ):
        continue
    os.environ.setdefault(node.args[0].value, node.args[1].value)

def unpack(obj):
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except ValueError:
            return obj
    return obj

def get_prediction(obj):
    obj = unpack(obj)
    if isinstance(obj, tuple) and obj:
        obj = unpack(obj[0])
    if isinstance(obj, dict) and "jsonData" in obj:
        obj = unpack(obj["jsonData"])
    if isinstance(obj, dict) and "prediction" in obj:
        obj = unpack(obj["prediction"])
    return obj

print("PZAAS ORIGINAL PYTORCH BASELINE: START", flush=True)
print("BASELINE PIPELINE IMPORT:", imports[0], flush=True)

started = time.monotonic()

try:
    with log.open("w") as output:
        with redirect_stdout(output), redirect_stderr(output):
            module_name, class_name = imports[0]
            Pipeline = getattr(
                importlib.import_module(module_name), class_name
            )

            pipeline = Pipeline()
            pipeline.load()

            # Deliberately no attach_max() and no MAX adapter.
            raw = pipeline.predict_raw(
                json.loads(fixture.read_text())
            )
except Exception as exc:
    print("PYTORCH BASELINE BLOCKED:", repr(exc))
    print("=== LAST 25 BASELINE LOG LINES ===")
    print("\n".join(log.read_text(errors="replace").splitlines()[-25:]))
    raise SystemExit(1)

print(
    "PYTORCH BASELINE EXECUTION: PASS",
    f"({time.monotonic()-started:.1f}s)",
    flush=True
)

max_prediction = get_prediction(
    json.loads(reference.read_text())
)
torch_prediction = get_prediction(raw)

print("MAX PREDICTION TYPE:", type(max_prediction).__name__)
print("PYTORCH PREDICTION TYPE:", type(torch_prediction).__name__)

if not isinstance(max_prediction, dict) or not isinstance(torch_prediction, dict):
    print("PYTORCH RAW TYPE:", type(raw).__name__)
    print("BUSINESS COMPARISON: BLOCKED BY RESPONSE SHAPE")
    raise SystemExit(1)

max_products = unpack(max_prediction.get("productList"))
torch_products = unpack(torch_prediction.get("productList"))

if not isinstance(max_products, list) or not isinstance(torch_products, list):
    print("BUSINESS COMPARISON: productList missing or invalid")
    print("PYTORCH KEYS:", list(torch_prediction)[:20])
    raise SystemExit(1)

def ids(items):
    return [
        item.get("productId") if isinstance(item, dict) else None
        for item in items
    ]

max_ids = ids(max_products)
torch_ids = ids(torch_products)

print("=== SAME-INPUT BUSINESS COMPARISON ===")
print("MAX PRODUCT COUNT:", len(max_products))
print("PYTORCH PRODUCT COUNT:", len(torch_products))
print("PRODUCT ID ORDER MATCH:", max_ids == torch_ids)
print("PRODUCT LIST EXACT MATCH:", max_products == torch_products)

for key in ("orig_score_value", "isNewRcmd"):
    print(
        key + " MATCH:",
        unpack(max_prediction.get(key))
        == unpack(torch_prediction.get(key))
    )

same_products = max_products == torch_products
same_ids = max_ids == torch_ids

result = {
    "fixture": "pzaas_adjusted_sanity_input.json",
    "environment": "same image; isolated network",
    "max_product_count": len(max_products),
    "pytorch_product_count": len(torch_products),
    "product_id_order_match": same_ids,
    "product_list_exact_match": same_products,
    "orig_score_value_match": (
        unpack(max_prediction.get("orig_score_value"))
        == unpack(torch_prediction.get("orig_score_value"))
    ),
    "isNewRcmd_match": (
        unpack(max_prediction.get("isNewRcmd"))
        == unpack(torch_prediction.get("isNewRcmd"))
    )
}

Path("/evidence/pzaas_business_comparison.json").write_text(
    json.dumps(result, indent=2)
)

print("=== BASELINE LOOKUP ERRORS ===")
lines = log.read_text(errors="replace").splitlines()
lookup_errors = [
    line for line in lines
    if "NameResolutionError" in line
    or "fetching error" in line
]
print("LOOKUP ERROR LOG ENTRIES:", len(lookup_errors))

print("=== FINAL RESULT ===")
if same_products:
    print("SAME-INPUT PRODUCT LIST PARITY: PASS")
elif same_ids:
    print("PRODUCT ID PARITY: PASS; FIELD DIFFERENCES REMAIN")
else:
    print("BUSINESS PARITY: NOT YET CONFIRMED")

print("COMPARISON SAVED: /evidence/pzaas_business_comparison.json")
print("ORIGINAL DS / WEIGHTS / MAX IMAGE: UNCHANGED")
PY
SH
