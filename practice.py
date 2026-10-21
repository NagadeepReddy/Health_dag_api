cat > artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py <<'PY'
"""Explicit CTA registration before launching native MAX Serve."""

import runpy
import shutil
import sys

from cta_worker_registration import install_cta_scheduler_hook

def main():
    install_cta_scheduler_hook()
    print("CTA native worker hook installed", flush=True)

    max_cli = shutil.which("max")
    if not max_cli:
        raise RuntimeError("MAX CLI not found")

    sys.argv = [max_cli, "serve", *sys.argv[1:]]
    runpy.run_path(max_cli, run_name="__main__")

if __name__ == "__main__":
    main()
PY
