python3 - <<'PY'
import subprocess, json

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"

r = subprocess.run(
    pod + ["inspect", name],
    capture_output=True, text=True, check=True
)
info = json.loads(r.stdout)[0]

print("=== ISOLATED SERVER ===")
print("STATUS:", info["State"]["Status"])
print("OOM KILLED:", info["State"].get("OOMKilled"))
print("MEMORY LIMIT GB:", round(info["HostConfig"]["Memory"]/1024**3, 2))

for port in (8766, 8765):
    r = subprocess.run(
        ["curl", "--noproxy", "*", "-s",
         "-o", "/dev/null", "-w", "%{http_code}",
         "--max-time", "10",
         f"http://127.0.0.1:{port}/health"],
        capture_output=True, text=True
    )
    print(f"MAX {port} HEALTH:", r.stdout.strip())

    if port == 8766 and r.stdout.strip() != "200":
        logs = subprocess.run(
            pod + ["logs", "--tail", "50", name],
            capture_output=True, text=True
        )
        print("=== STARTUP LOGS ===")
        print((logs.stdout + logs.stderr)[-7000:])

print("NO FILES MODIFIED")
PY
