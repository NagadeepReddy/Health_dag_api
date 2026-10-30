
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, re, json, shutil, subprocess, time, urllib.request, os
from pathlib import Path

root = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
pkg = root / "cta_max"
aux = pkg / "grecbase_aux_features_max.py"
graph = pkg / "grecbase_fusion_batch2_draft.py"

pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]
name = "cta-batch2-trace-8766-10g"

def run(args, timeout=60):
    return subprocess.run(args, capture_output=True,
                          text=True, timeout=timeout)

def original_health():
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8765/health", timeout=5
        ) as r:
            return r.status == 200
    except Exception:
        return False

print("=== SAFETY PRE-FLIGHT ===", flush=True)
assert original_health(), "STOP: Original MAX unhealthy"

r = run(pod + ["inspect", name])
assert r.returncode == 0, r.stderr
info = json.loads(r.stdout)[0]
assert info["State"]["Running"], "STOP: Isolated container not running"
assert not info["State"]["OOMKilled"], "STOP: OOM detected"
assert 9 <= info["HostConfig"]["Memory"] / 1024**3 <= 11, \
    "STOP: 10GB memory limit not verified"

assert any(
    m["Destination"] == "/batch2"
    and Path(m["Source"]).resolve() == root.resolve()
    for m in info["Mounts"]
), "STOP: Active Batch-2 mount mismatch"

available = int(re.search(
    r"MemAvailable:\s*(\d+)",
    Path("/proc/meminfo").read_text()
).group(1)) / 1024**2

assert available >= 12, "STOP: Host memory insufficient"
assert shutil.disk_usage(pkg).free > 30 * 1024**2, \
    "STOP: Insufficient application1 disk"

print("ORIGINAL MAX: HEALTHY")
print("MEMORY LIMIT: 10GB")
print("HOST AVAILABLE GB:", round(available, 2))

# Only five known batch-size mismatches in active files.
specs = {
    aux: [
        (
            "AUX POOL",
            r"\[\s*1\s*,\s*2\s*\*\s*dim\s*\]",
            r"\[\s*2\s*,\s*2\s*\*\s*dim\s*\]",
            "[2, 2 * dim]"
        ),
        (
            "AUX TASK",
            r"task\s*=\s*ops\.reshape\(\s*task\s*,\s*\[\s*1\s*,\s*256\s*\]\s*\)",
            r"task\s*=\s*ops\.reshape\(\s*task\s*,\s*\[\s*2\s*,\s*256\s*\]\s*\)",
            "task = ops.reshape(task, [2, 256])"
        ),
    ],
    graph: [
        (
            "SIBLING",
            r"ops\.reshape\(\s*value\s*,\s*\[\s*1\s*,\s*1\s*,\s*128\s*\]\s*\)",
            r"ops\.reshape\(\s*value\s*,\s*\[\s*2\s*,\s*1\s*,\s*128\s*\]\s*\)",
            "ops.reshape(value, [2, 1, 128])"
        ),
        (
            "VALID LENGTH",
            r"ops\.reshape\(\s*remaining\[\s*66\s*\]\s*,\s*\[\s*1\s*,\s*1\s*\]\s*\)",
            r"ops\.reshape\(\s*remaining\[\s*66\s*\]\s*,\s*\[\s*2\s*,\s*1\s*\]\s*\)",
            "ops.reshape(remaining[66], [2, 1])"
        ),
        (
            "FINAL FUSION",
            r"outs\s*=\s*ops\.reshape\(\s*outs\s*,\s*\[\s*1\s*,\s*2048\s*\]\s*\)",
            r"outs\s*=\s*ops\.reshape\(\s*outs\s*,\s*\[\s*2\s*,\s*2048\s*\]\s*\)",
            "outs = ops.reshape(outs, [2, 2048])"
        ),
    ]
}

print("\n=== VERIFY AND PREPARE ALL FIVE FIXES ===")
prepared = {}
changed = 0

for path, rules in specs.items():
    assert path.is_file(), f"STOP: Missing {path}"
    source = path.read_text()
    ast.parse(source, filename=str(path))
    updated = source

    for label, old, new, replacement in rules:
        old_count = len(re.findall(old, updated))
        new_count = len(re.findall(new, updated))

        if old_count == 1 and new_count == 0:
            updated = re.sub(old, replacement, updated, count=1)
            print(label, "FIX READY")
            changed += 1
        elif old_count == 0 and new_count == 1:
            print(label, "ALREADY FIXED")
        else:
            raise RuntimeError(
                f"STOP: Ambiguous {label}: "
                f"old={old_count}, new={new_count}"
            )

    ast.parse(updated, filename=str(path))
    prepared[path] = updated

print("TOTAL NEW FIXES:", changed)
if not changed:
    raise SystemExit("STOP: No new source correction needed")

# Back up both files before changing either one.
for path, updated in prepared.items():
    if updated == path.read_text():
        continue
    backup = path.with_name(path.name + ".before_batch2_shape_fix_v1")
    assert not backup.exists(), f"STOP: Backup already exists: {backup}"

for path, updated in prepared.items():
    if updated == path.read_text():
        continue
    backup = path.with_name(path.name + ".before_batch2_shape_fix_v1")
    shutil.copy2(path, backup)

for path, updated in prepared.items():
    if updated == path.read_text():
        continue
    temporary = path.with_name(path.name + ".batch2_temp_v1")
    assert not temporary.exists(), f"STOP: Temporary file exists: {temporary}"
    temporary.write_text(updated)
    ast.parse(temporary.read_text())
    os.replace(temporary, path)

print("BACKUPS: PRESERVED")
print("SYNTAX: PASS")
print("ISOLATED FILE FIXES: INSTALLED", flush=True)

# Restart only the isolated container.
print("\n=== ISOLATED RESTART ===", flush=True)
r = run(pod + ["restart", "--time", "15", name], timeout=90)
assert r.returncode == 0, "STOP: " + r.stderr

inside = r'''
import json, time, urllib.request, urllib.error, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)

healthy = False
for i in range(45):
    try:
        with opener.open(
            "http://127.0.0.1:8766/health", timeout=3
        ) as r:
            if r.status == 200:
                healthy = True
                break
    except Exception:
        time.sleep(2)

print("ISOLATED HEALTH:", "PASS" if healthy else "FAIL",
      flush=True)
if not healthy:
    raise SystemExit(2)

fixture = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "STOP: Real CTA JSON missing"
payload = fixture.read_bytes()
assert isinstance(json.loads(payload), dict)

barrier = threading.Barrier(2)

def request(n):
    try:
        barrier.wait(timeout=10)
        req = urllib.request.Request(
            "http://127.0.0.1:8766/v2/cta/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with opener.open(req, timeout=120) as r:
            body = json.loads(r.read())
            offers = body["jsonData"]["prediction"]["offerList"]
            if not isinstance(offers, list):
                return n, "INVALID RESPONSE", str(body)[:400]
            return n, "PASS", len(offers)
    except urllib.error.HTTPError as e:
        return n, "HTTP " + str(e.code), \
            e.read(1200).decode(errors="replace")
    except Exception as e:
        return n, "ERROR", repr(e)

with ThreadPoolExecutor(max_workers=2) as pool:
    a = pool.submit(request, 1)
    b = pool.submit(request, 2)
    results = sorted([a.result(), b.result()])

for result in results:
    print("REQUEST:", result, flush=True)

print(
    "REAL NATIVE HTTP 2/2:",
    "PASS" if all(r[1] == "PASS" for r in results)
    else "FAIL",
    flush=True
)
'''

print("\n=== TWO REAL CTA HTTP REQUESTS ===", flush=True)
try:
    r = run(
        pod + ["exec", "-e", "PYTHONDONTWRITEBYTECODE=1",
               name, "/opt/venv/bin/python", "-B", "-c", inside],
        timeout=230
    )
    print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr[-2500:], flush=True)
except subprocess.TimeoutExpired:
    print("HTTP VALIDATION: TIMEOUT")

print("\n=== NATIVE BATCH EVIDENCE ===")
r = run(pod + ["logs", "--tail", "350", name])
logs = r.stdout + r.stderr
markers = (
    "CTA TRUE MAX BATCH-2",
    "REAL MAX BATCH-2",
    "CTA RESPONSE ID MATCH",
    "CTA RESPONSE WORKER",
    "RESHAPE",
    "reshape",
    "Error",
    "ERROR",
    "Traceback",
    "POST /v2/cta/predict"
)
selected = [
    line for line in logs.splitlines()
    if any(m in line for m in markers)
]
print("\n".join(selected[-35:]) or "NO MATCHING LOGS")

print("\n=== FINAL SAFETY ===")
print("ORIGINAL MAX:",
      "HEALTHY" if original_health() else "CHECK REQUIRED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")
print("BACKUPS: PRESERVED")
PY
