PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, re, shutil, subprocess, time, sys
from pathlib import Path
from datetime import datetime, timezone

root = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
pkg = root / "cta_max"

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"

def run(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, **kw)

info = run(pod + ["inspect", name])
if info.returncode:
    sys.exit("STOP: Isolated container missing")

c = json.loads(info.stdout)[0]

if c["HostConfig"]["Memory"] != 10737418240:
    sys.exit("STOP: 10 GB memory limit not verified")

if not any(
    m["Destination"] == "/batch2"
    and Path(m["Source"]).resolve() == root.resolve()
    for m in c["Mounts"]
):
    sys.exit("STOP: Active Batch-2 mount differs")

available = next(
    int(x.split()[1])
    for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)

if available < 12582912:
    sys.exit("STOP: Host memory safety threshold")

# Only verified Batch-2 candidate shape sites.
specs = {
    "grecbase_aux_features_max.py": [
        (r"(\bops\.reshape\(\s*ops\.concat\(\s*\[\s*mean\s*,\s*maximum\s*\]\s*,\s*axis\s*=\s*1\s*\)\s*,\s*)\[\s*1\s*,\s*2\s*\*\s*dim\s*\]",
         r"\g<1>[2, 2 * dim]"),
        (r"(\bops\.reshape\(\s*task\s*,\s*)\[\s*1\s*,\s*256\s*\]",
         r"\g<1>[2, 256]"),
        (r"(\bops\.reshape\(\s*jet0\s*,\s*)\[\s*1\s*,\s*1\s*,\s*128\s*\]",
         r"\g<1>[2, 1, 128]"),
        (r"(\bops\.reshape\(\s*jet1\s*,\s*)\[\s*1\s*,\s*1\s*,\s*128\s*\]",
         r"\g<1>[2, 1, 128]")
    ],
    "grecbase_fusion_batch2_draft.py": [
        (r"(\bops\.reshape\(\s*value\s*,\s*)\[\s*1\s*,\s*1\s*,\s*128\s*\]",
         r"\g<1>[2, 1, 128]"),
        (r"(\bops\.reshape\(\s*remaining\[66\]\s*,\s*)\[\s*1\s*,\s*1\s*\]",
         r"\g<1>[2, 1]"),
        (r"(\bops\.reshape\(\s*x\s*,\s*)\[\s*1\s*,\s*1\s*,\s*256\s*\]",
         r"\g<1>[2, 1, 256]"),
        (r"(\bops\.reshape\(\s*outs\s*,\s*)\[\s*1\s*,\s*2048\s*\]",
         r"\g<1>[2, 2048]")
    ]
}

changes = {}

for filename, rules in specs.items():
    path = pkg / filename
    if not path.is_file():
        sys.exit(f"STOP: Missing candidate {filename}")

    original = path.read_text()
    updated = original

    for pattern, replacement in rules:
        updated, count = re.subn(pattern, replacement, updated)
        if count > 1:
            sys.exit(f"STOP: Ambiguous shape in {filename}")

    compile(updated, str(path), "exec")
    if updated != original:
        changes[path] = updated

print("=== BATCH-2 REPAIR ===")

if not changes:
    sys.exit("STOP: No matching shapes; do not repeat restart")

# Back up before changing anything.
stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

for path in changes:
    backup = path.with_name(path.name + ".before_batch2_" + stamp)
    shutil.copy2(path, backup)
    print("BACKUP:", backup)

for path, updated in changes.items():
    path.write_text(updated)
    print("PATCHED:", path.name)

print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")

r = run(pod + ["restart", "--time", "15", name], timeout=90)
if r.returncode:
    sys.exit("STOP: Isolated restart failed: " + r.stderr[-500:])

print("ISOLATED RESTART: PASS", flush=True)

test = r'''
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8766"

for n in range(60):
    try:
        with urllib.request.urlopen(base + "/health", timeout=2) as r:
            if r.status == 200:
                break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit("STOP: Isolated health failed")

print("HEALTH: PASS", flush=True)

p = Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
if not p.is_file():
    raise SystemExit("STOP: CTA fixture missing")

data = p.read_bytes()
json.loads(data)

def send(n):
    req = urllib.request.Request(
        base + "/v2/cta/predict",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return n, r.status, r.read(1200).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return n, e.code, e.read(1200).decode(errors="replace")
    except Exception as e:
        return n, "ERROR", repr(e)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, status, body in results:
    print(f"REQUEST {n}: {status}", flush=True)
    if status != 200:
        print(body[:1200], flush=True)

print(
    "NATIVE HTTP 2/2:",
    "PASS" if all(x[1] == 200 for x in results)
    else "NOT PASSED",
    flush=True
)
'''

r = subprocess.run(
    pod + ["exec", "-i", name, "/opt/venv/bin/python", "-B", "-c", test],
    capture_output=True, text=True, timeout=180
)

print(r.stdout)
if r.returncode or "NOT PASSED" in r.stdout:
    print(r.stderr[-1000:])
    logs = run(pod + ["logs", "--tail", "100", name])
    interesting = [
        x for x in (logs.stdout + logs.stderr).splitlines()
        if any(k in x.lower() for k in
               ("reshape", "error", "traceback", "batch", "worker failed"))
    ]
    print("\n=== LATEST FAILURE EVIDENCE ===")
    print("\n".join(interesting[-12:]))
else:
    print("HTTP VALIDATION: PASS")
    print("BACKEND COALESCING: REQUIRES LOG CONFIRMATION")

print("ORIGINAL DS/MAX: UNCHANGED")
PY
