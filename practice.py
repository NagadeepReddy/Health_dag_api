
python3 - <<'PY'
from pathlib import Path
import ast

folder = Path("artifacts/v1.168-max/maxserve_cta_extension/bootstrap")
p = folder / "sitecustomize.py"

code = '''
"""Opt-in CTA hook initialization for MAX Serve Python processes."""

import os

if os.environ.get("CTA_MAX_NATIVE_BOOTSTRAP") == "1":
    import sys
    from pathlib import Path

    extension_root = str(Path(__file__).resolve().parents[2])
    if extension_root not in sys.path:
        sys.path.insert(0, extension_root)

    from maxserve_cta_extension.cta_worker_registration import (
        install_cta_scheduler_hook,
    )

    install_cta_scheduler_hook()
'''

ast.parse(code)
folder.mkdir(parents=True, exist_ok=True)

with p.open("x") as f:
    f.write(code)

print("CTA SPAWN BOOTSTRAP CREATED — SYNTAX PASS")
print("BOOTSTRAP DEFAULT: DISABLED")
print("Original DS, MAX inference and installed MAX files unchanged")
PY
