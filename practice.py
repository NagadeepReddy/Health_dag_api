python3 - <<'PY'
from pathlib import Path
import json
import re

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
core = root / "artifacts/v1.113/core-artifact"
actual = Path("/tmp/bplan_myplan_trace.json")
expected = core / "test_samples/test_sample_myplan_bundle_output.json"

print("=== ORIGINAL DS DEFAULT DEFINITIONS ===")
symbols = (
    "DEFAULT_PROPOSITION_LIST_BPLAN",
    "CURRENT_PROPOSITION_LIST_TAB",
    "CURRENT_PROPOSITION_LIST_CD",
)

for p in sorted(core.rglob("*.py")):
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if any(re.match(r"^\s*" + name + r"\s*=", line)
               for name in symbols):
            print(f"\nFILE: {p.relative_to(core)} LINE: {i+1}")
            for j in range(i, min(i+12, len(lines))):
                print(f"{j+1}: {lines[j][:180]}")

print("\n=== MYPLAN EXPECTED VS CURRENT ===")

for label, p in (("EXPECTED", expected), ("CURRENT MAX HTTP", actual)):
    if not p.is_file():
        print(label, "MISSING")
        continue

    obj = json.loads(p.read_text())
    data = obj.get("jsonData", {})
    if isinstance(data, str):
        data = json.loads(data)

    meta = obj.get("transactionMetadata", {})
    print(f"\n{label}")
    print("INFERENCE RECORDED:", isinstance(meta, dict) and "inference" in meta)

    lists = data.get("prediction", {}).get("ctaList", [])
    for i, group in enumerate(lists):
        if isinstance(group, list):
            print("LIST", i, "COUNT", len(group),
                  "IDS", [x.get("propositionId") for x in group
                          if isinstance(x, dict)])
PY
