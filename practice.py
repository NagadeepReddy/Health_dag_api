python3 - <<'PY'
import subprocess

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"

r = subprocess.run(
    pod + ["inspect", "--format",
           "{{.State.Status}} ExitCode={{.State.ExitCode}}", name],
    capture_output=True, text=True
)
print("ISOLATED CONTAINER:", r.stdout.strip() or r.stderr.strip())

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
            pod + ["logs", "--tail", "70", name],
            capture_output=True, text=True
        )
        print("=== ISOLATED STARTUP ERROR ===")
        print((logs.stdout + logs.stderr)[-10000:])

print("ORIGINAL DS: UNCHANGED")
PY
