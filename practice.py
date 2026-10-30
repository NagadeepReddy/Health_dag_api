
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, json, shutil, subprocess, time
import urllib.request, urllib.error
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
adapter = base / "native_batch2_cached_overlay/cta_worker_adapter.py"
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
relative = "artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy"
payload = repo / "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
name = "cta-batch2-trace-8766-10g"
pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

def run(*args, timeout=45):
    return subprocess.run(pod + list(args), capture_output=True,
                          text=True, timeout=timeout)

def healthy(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=3
        ) as r:
            return r.status == 200
    except Exception:
        return False

def recent_logs():
    r = run("logs", "--tail", "75", name)
    print("\n=== ISOLATED LOGS ===")
    print("\n".join((r.stdout + r.stderr).splitlines()[-45:]))

print("=== SAFETY AND SOURCE CHECK ===", flush=True)
r = run("inspect", name)
assert r.returncode == 0, "Isolated container missing"
info = json.loads(r.stdout)[0]
mounts = {m["Destination"]: m["Source"] for m in info["Mounts"]}

assert healthy(8765), "STOP: Original MAX unhealthy"
assert adapter.is_file(), "STOP: Isolated adapter missing"
assert (repo / relative).is_file(), "STOP: Original weight missing"
assert payload.is_file(), "STOP: CTA input missing"
assert mounts.get("/workspace") == str(repo), "STOP: Unexpected workspace mount"
assert info["State"]["Status"] == "running", "STOP: Container not running"
assert not info["State"].get("OOMKilled"), "STOP: Previous OOM"
assert 9 <= info["HostConfig"]["Memory"] / 1024**3 <= 12

r = run("exec", name, "test", "-f", "/workspace/" + relative)
assert r.returncode == 0, "STOP: Weight not accessible inside container"

source = adapter.read_text()
tree = ast.parse(source)
methods = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == "predict_batch"]
assert len(methods) == 1, "STOP: Unexpected adapter structure"

marker = "# CTA_WORKER_CWD_FIX_V1"
if marker not in source:
    node = methods[0]
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(
        getattr(first, "value", None), ast.Constant
    ) and isinstance(first.value.value, str):
        line = first.end_lineno + 1
    else:
        line = first.lineno

    lines = source.splitlines(keepends=True)
    indent = " " * first.col_offset
    fix = (
        f"{indent}{marker}\n"
        f"{indent}import os as _cta_os\n"
        f"{indent}_cta_os.chdir('/workspace')\n"
    )
    updated = "".join(lines[:line-1]) + fix + "".join(lines[line-1:])
    ast.parse(updated)

    backup = adapter.with_name("cta_worker_adapter.py.before_cwd_fix")
    assert not backup.exists(), "STOP: Backup already exists"
    assert shutil.disk_usage(base).free > 512 * 1024**2

    print("STOPPING ISOLATED CONTAINER ONLY", flush=True)
    r = run("stop", "--time", "15", name)
    assert r.returncode == 0, r.stderr

    shutil.copy2(adapter, backup)
    adapter.write_text(updated)
    print("ISOLATED WORKER CWD FIX: INSTALLED", flush=True)
else:
    print("WORKER CWD FIX: ALREADY INSTALLED", flush=True)
    raise SystemExit("STOP: Existing fix needs verification; no repeated restart")

print("RESTARTING ISOLATED CONTAINER ONLY", flush=True)
r = run("start", name)
assert r.returncode == 0, r.stderr

ready = False
for _ in range(20):
    if healthy(8766):
        ready = True
        break
    time.sleep(3)

if not ready:
    recent_logs()
    raise SystemExit("STOP: Isolated MAX not ready")

print("ISOLATED HTTP HEALTH: PASS", flush=True)
req = urllib.request.Request(
    "http://127.0.0.1:8766/v2/cta/predict",
    data=payload.read_bytes(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=240) as response:
        result = json.load(response)
        offers = result["jsonData"]["prediction"]["offerList"]
        assert isinstance(offers, list)
        print("REAL CTA HTTP: PASS")
        print("OFFERS:", len(offers))
except Exception as exc:
    print("REAL CTA HTTP: FAILED", repr(exc))
    if isinstance(exc, urllib.error.HTTPError):
        print(exc.read(1000).decode(errors="replace"))
    recent_logs()

print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")
PY
