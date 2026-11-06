
cd /application1/sajjna8 && python3 - <<'PY'
import json
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

base = Path("/application1/sajjna8")
runner = base / "max_shared_infra/bin/run_max_model_shared.sh"

models = {
    "CTA": {
        "package": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
        "route": "/v2/cta/predict",
    },
    "BPLAN": {
        "package": Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
        "route": "/bplan/predict",
    },
    "PZAAS": {
        "package": base / "PZAAS_MAX_CLEAN_HANDOFF_20261106",
        "route": "/pzaas/predict",
    },
}

print("=== SIMULTANEOUS THREE-MODEL SHARED MAX ===", flush=True)

if not runner.is_file():
    raise SystemExit("STOP: Shared runner missing")

def find_request(name, package):
    if name == "CTA":
        path = base / (
            "rt-pzaas-cta-offers-v1/artifacts/v1.168-max/"
            "cta_native_adjusted_sanity_input.json"
        )
        if path.is_file():
            return json.loads(path.read_text())

    if name == "BPLAN":
        paths = list(package.rglob("test_sample_1.json"))
        paths += list(
            (base / "rt-pzai-bplan-v1").rglob("test_sample_1.json")
        ) if (base / "rt-pzai-bplan-v1").is_dir() else []
        for path in paths:
            try:
                body = json.loads(path.read_text())
                if isinstance(body, dict):
                    return body
            except Exception:
                continue

    if name == "PZAAS":
        paths = [
            base / (
                "rt-pzaas-v1.0/artifacts/v1.472-max/"
                "maxserve_pzaas_extension/pzaas_http_evidence/"
                "PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json"
            )
        ]
        paths += list(package.rglob("*POSTMAN_COLLECTION.json"))

        def requests(items):
            for item in items:
                if "request" in item:
                    yield item["request"]
                yield from requests(item.get("item", []))

        for path in paths:
            if not path.is_file():
                continue
            try:
                collection = json.loads(path.read_text())
                for request in requests(collection.get("item", [])):
                    raw = request.get("body", {}).get("raw")
                    if raw:
                        body = json.loads(raw)
                        if isinstance(body, dict):
                            return body
            except Exception:
                continue

    return None

print("\n=== CONFIGURATION PREFLIGHT ===", flush=True)

ready = True
ports = set()

for name, data in models.items():
    package = data["package"]
    config = package / "config/model.env"

    if not config.is_file():
        print(f"{name}: BLOCKED - shared model.env missing")
        ready = False
        continue

    check = subprocess.run(
        ["bash", str(runner), "check", str(package)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if check.returncode != 0:
        print(f"{name}: PREFLIGHT BLOCKED")
        print(check.stdout[-1000:])
        ready = False
        continue

    port_result = subprocess.run(
        [
            "bash", "-c",
            'source "$1"; printf "%s" "${HOST_PORT:-18781}"',
            "bash", str(config),
        ],
        capture_output=True,
        text=True,
    )

    try:
        port = int(port_result.stdout.strip())
        assert 1024 <= port <= 65535
        assert port not in ports
        ports.add(port)
        data["port"] = port
    except Exception:
        print(f"{name}: BLOCKED - invalid or duplicate host port")
        ready = False
        continue

    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))
    except OSError:
        print(f"{name}: BLOCKED - host port {port} already occupied")
        ready = False
        continue

    data["body"] = find_request(name, package)
    if data["body"] is None:
        print(f"{name}: BLOCKED - verified JSON request not located")
        ready = False
        continue

    print(f"{name}: READY | PORT {port}", flush=True)

if not ready:
    raise SystemExit(
        "\nSTOP: Fix the reported shared configuration or request "
        "before starting three models. No containers started."
    )

mem_available = 0
for line in Path("/proc/meminfo").read_text().splitlines():
    if line.startswith("MemAvailable:"):
        mem_available = int(line.split()[1]) * 1024
        break

if mem_available < 20 * 1024**3:
    raise SystemExit(
        "STOP: Less than 20 GiB available; simultaneous "
        "startup could exhaust VM memory."
    )

processes = {}
results = {}

try:
    print("\n=== START ALL THREE CONCURRENTLY ===", flush=True)

    for name, data in models.items():
        log = open(f"/tmp/shared_max_{name.lower()}_combined.log", "w")
        proc = subprocess.Popen(
            ["bash", str(runner), "start", str(data["package"])],
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log.close()
        processes[name] = proc
        print(f"{name}: START REQUESTED", flush=True)

    deadline = time.monotonic() + 300
    pending = set(models)

    while pending and time.monotonic() < deadline:
        for name in list(pending):
            proc = processes[name]
            port = models[name]["port"]

            if proc.poll() is not None:
                raise RuntimeError(
                    f"{name} exited during startup: {proc.returncode}"
                )

            try:
                with socket.create_connection(
                    ("127.0.0.1", port), timeout=1
                ):
                    print(f"{name}: SERVER READY", flush=True)
                    pending.remove(name)
            except OSError:
                pass

        if pending:
            time.sleep(2)

    if pending:
        raise RuntimeError(f"Startup timeout: {sorted(pending)}")

    print("\n=== ALL THREE SERVERS ARE RUNNING ===", flush=True)

    for name, data in models.items():
        url = (
            f"http://127.0.0.1:{data['port']}"
            f"{data['route']}"
        )
        payload = json.dumps(data["body"]).encode()

        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=240
            ) as response:
                status = response.status
                body = json.loads(response.read())

            valid = (
                status == 200
                and isinstance(body, (dict, list))
                and bool(body)
                and not (
                    isinstance(body, dict)
                    and ("error" in body or "detail" in body)
                )
            )

            results[name] = valid
            print(
                f"{name}: HTTP {status} | "
                f"JSON {'PASS' if valid else 'BLOCKED'}",
                flush=True
            )

        except Exception as error:
            results[name] = False
            print(f"{name}: HTTP BLOCKED - {error}", flush=True)

    print("\n=== FINAL RESULT ===", flush=True)

    if all(results.get(name) for name in models):
        print("SIMULTANEOUS CTA + BPLAN + PZAAS: PASS")
        print("SHARED MAX THREE-MODEL HTTP: PASS")
    else:
        print("THREE-MODEL HTTP: NOT YET VERIFIED")
        for name, passed in results.items():
            print(name, "PASS" if passed else "BLOCKED")

finally:
    print("\n=== STOP ONLY TEST PROCESSES ===", flush=True)

    for proc in processes.values():
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    for proc in processes.values():
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    for name, passed in results.items():
        if not passed:
            log = Path(f"/tmp/shared_max_{name.lower()}_combined.log")
            if log.is_file():
                print(f"\n=== {name} LAST LOG LINES ===")
                print("\n".join(
                    log.read_text(errors="replace").splitlines()[-18:]
                ))

    print("ORIGINAL MODEL/HANDOFF FILES: UNCHANGED")
    print("TEST PROCESSES: STOPPED")
PY
