
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
test -d "$STAGE" || {
  echo "STOP: Clean stage missing"
  exit 1
}

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/source:ro" \
  -v "$STAGE:/stage:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /source \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import os
import subprocess
import sys

test_code = """
import traceback
try:
    from max.serve.scheduler.queues import SchedulerZmqConfigs
    from transformers import AutoTokenizer
    print("MAX + AUTOTOKENIZER IMPORT: PASS")
except BaseException:
    traceback.print_exc()
    raise SystemExit(1)
"""

for label, root in [
    ("WORKING ORIGINAL REPOSITORY", "/source"),
    ("NEW CLEAN STAGE", "/stage")
]:
    print(f"\n=== {label} ===", flush=True)

    paths = [
        "/shared_deps/sklearn161",
        "/shared_deps",
        f"{root}/artifacts/v1.472-max/pzaas_max/validation/python_deps",
        f"{root}/artifacts/v1.472-max/maxserve_pzaas_extension",
        f"{root}/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev",
        f"{root}/artifacts/v1.472-max",
        f"{root}/artifacts/v1.472/core-artifact",
        f"{root}/artifacts/v1.472/utils/dependency-utils"
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = ":".join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, "-u", "-c", test_code],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=90
    )

    if result.returncode == 0:
        print("IMPORT STATUS: PASS")
        continue

    print("IMPORT STATUS: FAILED")
    lines = result.stderr.splitlines()

    print("--- ROOT EXCEPTION / TRACEBACK ---")
    if len(lines) <= 85:
        print("\n".join(lines))
    else:
        print("\n".join(lines[:65]))
        print(f"... {len(lines)-85} intermediate lines omitted ...")
        print("\n".join(lines[-20:]))

print("\n=== COMPARISON COMPLETE: NO FILES MODIFIED ===")
PY
SH
