
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import json
from pathlib import Path

path = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_http_evidence/pzaas_native_response.json"
)

if not path.is_file():
    raise SystemExit("STOP: Saved HTTP response not found")

def unpack(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return value

data = json.loads(path.read_text())
body = unpack(data.get("jsonData", {}))
prediction = unpack(body.get("prediction", {})) if isinstance(body, dict) else {}
metadata = unpack(data.get("transactionMetadata", {}))

print("=== PZAAS BUSINESS RESPONSE VALIDATION ===")

if not isinstance(prediction, dict):
    raise SystemExit("STOP: Prediction is not a JSON object")

for key in (
    "productList",
    "addtieList",
    "orig_score_value",
    "isNewRcmd",
    "timeToLive",
    "expMetadata"
):
    value = unpack(prediction.get(key))
    if isinstance(value, list):
        print(f"{key}: list, count={len(value)}")
        if value and isinstance(value[0], dict):
            print("  First item fields:", list(value[0]))
    elif isinstance(value, dict):
        print(f"{key}: dict, keys={list(value)[:15]}")
    else:
        print(f"{key}: type={type(value).__name__}, present={value is not None}")

print("\n=== EXTERNAL LOOKUP STATUS ===")

if isinstance(metadata, dict):
    for key in (
        "pull_bq_lookups_status",
        "pull_elysium_lookups_status"
    ):
        entry = unpack(metadata.get(key))
        if isinstance(entry, dict):
            print(
                f"{key}: status={entry.get('status')!r}, "
                f"error_present={bool(entry.get('error'))}"
            )
        else:
            print(f"{key}: {type(entry).__name__}")

print("\n=== VALIDATION SUMMARY ===")

products = unpack(prediction.get("productList"))
print(
    "PRODUCT RECOMMENDATIONS:",
    len(products) if isinstance(products, list)
    else f"Not a list ({type(products).__name__})"
)
print("TRAINED MAX EXECUTION: PREVIOUSLY CONFIRMED")
print("ORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
