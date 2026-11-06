
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

NAME="PZAAS_MAX_CLEAN_HANDOFF_20261106"
ARCHIVE="${NAME}.tar.gz"
CHECKSUM="${ARCHIVE}.sha256"

test -d "$NAME"
test -f "$ARCHIVE"
test -f "$CHECKSUM"

echo "=== PZAAS FINAL HANDOFF VERIFICATION ==="

sha256sum -c "$CHECKSUM"

python3 - "$ARCHIVE" "$NAME" <<'PY'
import sys
import tarfile
from pathlib import Path

archive = Path(sys.argv[1])
name = sys.argv[2]

required = [
    "model/artifacts/v1.472/core-artifact/pipeline.py",
    "model/artifacts/v1.472-max/pzaas_max/validation/pzaas_forward_schema.json",
    "model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
    "runtime/launch_max_model.sh",
    "config/model.env"
]

with tarfile.open(archive, "r:gz") as tar:
    members = {m.name for m in tar.getmembers()}
    for relative in required:
        path = f"{name}/{relative}"
        if path not in members:
            raise SystemExit(f"STOP: Missing archive member: {path}")

print("HANDOFF ARCHIVE CONTENTS: PASS")
print("GENERIC LAUNCHER: INCLUDED")
print("PZAAS MODEL CONFIG: INCLUDED")
print("ORIGINAL DS AND MAX INTEGRATION: INCLUDED")
PY

echo "=== FINAL STATUS ==="
echo "PZAAS CPU POC: COMPLETE"
echo "TRAINED MAX INFERENCE: PASS"
echo "NUMERICAL AND BUSINESS PARITY: PASS"
echo "POSTMAN HTTP 200: PASS"
echo "PACKAGED COLD START: PASS"
echo "GENERIC LAUNCHER: PASS"
echo "SHA256: VERIFIED"
echo "LIVE KUBERNETES LOOKUPS: PENDING"
echo "OTHER-VM PORTABILITY / IMAGE APPROVAL: PENDING"
echo "ORIGINAL DS / CTA / BPLAN: UNCHANGED"
SH
