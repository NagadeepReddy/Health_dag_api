python3 - <<'PY'
import json, re
from pathlib import Path

out = Path("artifacts/v1.168-max/test-results")
text = Path("/tmp/cta_pytorch_tiles_response.json").read_text()
decoder = json.JSONDecoder()

pt = None
for m in re.finditer(r'\{\s*"jsonData"\s*:', text):
    try:
        pt, _ = decoder.raw_decode(text[m.start():])
        break
    except json.JSONDecodeError:
        pass

if pt is None:
    raise SystemExit("PyTorch response not found")

mx = json.loads((out / "cta_max_tiles_response.json").read_text())
match = pt["jsonData"]["prediction"] == mx["jsonData"]["prediction"]

(out / "cta_pytorch_tiles_response.json").write_text(json.dumps(pt, indent=2))
(out / "cta_parity_result.txt").write_text(
    f"Modified Tiles smoke test\n"
    f"MAX vs PyTorch full prediction exact match: {match}\n"
)

print("PYTORCH BASELINE SAVED")
print("FULL PREDICTION EXACT MATCH:", match)
print("COMPARISON EVIDENCE SAVED")
PY
