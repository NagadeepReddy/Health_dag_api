
cd /application1/sajjna8 && python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8")
repo = root / "rt-pzaas-v1.0"

locations = [
    repo / "artifacts/v1.472/samples",
    repo / "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence",
    root / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/artifacts/v1.472/samples",
]

print("=== FIND ORIGINAL PZAAS HTTP REQUEST ===")

for folder in locations:
    print("\nLOCATION:", folder)
    if not folder.is_dir():
        print("NOT PRESENT")
        continue

    files = sorted(folder.glob("*.json"))
    print("JSON FILES:", len(files))

    for path in files[:30]:
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            print(path.name, "UNREADABLE:", str(exc)[:100])
            continue

        print("\nFILE:", path.name)

        if isinstance(data, dict):
            print("TOP LEVEL:", list(data)[:12])
            print("JSON DATA:", "jsonData" in data)
            print("POSTMAN COLLECTION:", "item" in data)

            if "item" in data:
                def walk(items):
                    for item in items:
                        req = item.get("request")
                        if isinstance(req, dict):
                            body = req.get("body", {})
                            raw = body.get("raw") if isinstance(body, dict) else None
                            if raw:
                                try:
                                    parsed = json.loads(raw)
                                    print(
                                        "  REQUEST:",
                                        item.get("name"),
                                        "KEYS:",
                                        list(parsed)[:10]
                                        if isinstance(parsed, dict)
                                        else type(parsed).__name__
                                    )
                                except (ValueError, TypeError):
                                    print("  REQUEST:", item.get("name"),
                                          "RAW BODY NOT DIRECT JSON")
                        walk(item.get("item", []))
                walk(data.get("item", []))

        elif isinstance(data, list):
            print("LIST ITEMS:", len(data))
            if data and isinstance(data[0], dict):
                print("FIRST ITEM KEYS:", list(data[0])[:12])

print("\n=== RESULT ===")
print("NO FILES MODIFIED")
print("NO CONTAINERS STARTED")
print("NEXT: VALIDATE SHARED MAX LIVE HTTP USING ORIGINAL INPUT")
PY
