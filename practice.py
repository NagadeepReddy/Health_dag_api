python3 - <<'PY'
import json, re, socket, subprocess
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
old = str(base / "native_batch2_minimal_overlay")
new = str(base / "native_batch2_cached_overlay")

assert (Path(new) / "cta_native_batch2_proven_server.py").is_file()

with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", 8766)) != 0, "STOP: Port 8766 occupied"

cgroup = Path("/proc/326785/cgroup").read_text()
cid = re.search(r"libpod-([0-9a-f]{64})\.scope", cgroup)
assert cid, "STOP: Live server identity unavailable"

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

raw = subprocess.check_output(
    pod + ["inspect", "--format",
           "{{json .Config.CreateCommand}}", cid.group(1)],
    text=True
)

cmd = json.loads(raw)

assert cmd[:len(pod)] == pod
assert "run" in cmd
assert "--rm" in cmd
assert "--read-only" in cmd
assert "--pull=never" in cmd

matches = [
    i for i, arg in enumerate(cmd)
    if arg.startswith(old + ":")
]

assert len(matches) == 1, "STOP: Overlay mount mismatch"
cmd[matches[0]] = cmd[matches[0]].replace(old, new, 1)

print("OPTIMIZED TEST SERVER: STARTING ON 8766", flush=True)
print("WORKING SERVER 8765: UNCHANGED", flush=True)

subprocess.run(cmd, check=True)
PY
