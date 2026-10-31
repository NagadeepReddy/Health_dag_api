python3 -B - <<'PY'
from pathlib import Path
import subprocess

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")

if not root.is_dir():
    raise SystemExit("STOP: Clean VM folder missing")

available_kb = int(next(
    x.split()[1]
    for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
))

print(f"AVAILABLE RAM: {available_kb / 1024 / 1024:.1f} GiB", flush=True)

if available_kb < 20 * 1024 * 1024:
    raise SystemExit("STOP: Less than 20 GiB available RAM")

code = r'''
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

launch = (
    "from maxserve_cta_extension.cta_queue_compat import install; "
    "assert install(); "
    "from maxserve_cta_extension.cta_native_launcher import main; "
    "main()"
)

cmd = [
    sys.executable, "-B", "-u", "-c", launch,
    "--port", "18767",
    "--model-path", "/workspace/artifacts/v1.168-max/cta_native_model",
    "--devices", "cpu",
    "--max-batch-size", "2"
]

log_path = Path("/tmp/cta_clean_test.log")
log = log_path.open("w")
server = None
passed = False

try:
    server = subprocess.Popen(
        cmd,
        stdout=log,
        stderr=subprocess.STDOUT
    )

    ready = False

    for _ in range(240):
        if server.poll() is not None:
            break

        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:18767/health",
                timeout=2
            ) as response:
                if response.status == 200:
                    ready = True
                    break
        except Exception:
            pass

        time.sleep(1)

    if not ready:
        raise RuntimeError("Clean native server did not become ready")

    print("CLEAN NATIVE SERVER: READY", flush=True)

    fixture = Path(
        "/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
    )

    if not fixture.is_file():
        raise RuntimeError(f"CTA fixture missing: {fixture}")

    payload = json.loads(fixture.read_text())

    request = urllib.request.Request(
        "http://127.0.0.1:18767/v2/cta/predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read())

        print("CLEAN CTA HTTP:", response.status)
        print("RESPONSE FIELDS:", sorted(result.keys()))

        assert response.status == 200
        assert result

    print("CLEAN NATIVE CTA REQUEST: PASS", flush=True)
    passed = True

except Exception as exc:
    print("CLEAN NATIVE CTA REQUEST: FAIL", repr(exc), flush=True)
    log.flush()

    if log_path.exists():
        lines = log_path.read_text(errors="replace").splitlines()
        print("LAST SERVER LOG LINES:")
        print("\n".join(lines[-35:]))

finally:
    if server is not None and server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    log.close()
    print("ISOLATED TEST SERVER: STOPPED", flush=True)

if not passed:
    sys.exit(1)
'''

cmd = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
    "run",
    "--rm",
    "-i",
    "--pull=never",
    "--network=none",
    "--read-only=false",
    "--memory=14g",
    "--memory-swap=14g",
    "--cpus=4",
    "--pids-limit=256",
    "--tmpfs", "/tmp:rw,size=2g,mode=1777",
    "--tmpfs", "/root:rw,size=64m",
    "-e", "PYTHONDONTWRITEBYTECODE=1",
    "-e", "PYTHONUNBUFFERED=1",
    "-e", "HOME=/tmp",
    "-e", "TMPDIR=/tmp",
    "-e", "XDG_CACHE_HOME=/tmp/cta_cache",
    "-e", "HF_HOME=/tmp/cta_cache",
    "-e", "TORCH_HOME=/tmp/cta_cache",
    "-e", "CUDA_VISIBLE_DEVICES=",
    "-e", "OTEL_SDK_DISABLED=true",
    "-e", "OTEL_METRICS_EXPORTER=none",
    "-e", "OTEL_TRACES_EXPORTER=none",
    "-e", "OTEL_LOGS_EXPORTER=none",
    "-e",
    "PYTHONPATH=/workspace/artifacts/v1.168-max/cta_native_batch2_release_candidate:/workspace/artifacts/v1.168/core-artifact:/batch2:/workspace/artifacts/v1.168-max",
    "-v", f"{root}:/workspace:ro",
    "-v", f"{root}/batch2:/batch2:ro",
    "--entrypoint", "/opt/venv/bin/python",
    "localhost/cta-max-faiss:local",
    "-B", "-"
]

print("STARTING ISOLATED CLEAN CTA TEST", flush=True)

result = subprocess.run(cmd, input=code, text=True)

print("CONTAINER EXIT CODE:", result.returncode, flush=True)

raise SystemExit(result.returncode)
PY
