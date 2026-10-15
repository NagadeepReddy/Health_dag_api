python3 - <<'PY'
import json
from pathlib import Path

for name in ["cta_pytorch_tiles_response.json", "cta_max_tiles_response.json"]:
    p = Path("/tmp") / name
    text = p.read_text() if p.exists() else ""
    print("\nFILE:", name)
    print("SIZE:", len(text))
    try:
        data = json.loads(text)
        print("JSON: VALID")
        print("TOP-LEVEL KEYS:", list(data) if isinstance(data, dict) else type(data).__name__)
    except Exception as e:
        print("JSON: INVALID —", str(e))
        print("START:", repr(text[:200]))
PY
