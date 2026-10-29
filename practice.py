cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
import tarfile
from pathlib import Path

archive = Path(
    "/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz"
)
stage = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2_live_stage"
)

assert archive.is_file()
assert stage.is_dir()

with tarfile.open(archive, "r:gz") as tar:
    for name in (
        "cta_native_live_server.py",
        "cta_native_http_entry.py",
        "cta_native_e2e_test.py",
    ):
        member = tar.getmember("release_candidate/" + name)
        source = tar.extractfile(member).read().decode()
        lines = source.splitlines()

        print("\n=== WORKING:", name, "===")

        if name == "cta_native_live_server.py":
            selected = range(min(115, len(lines)))
        elif name == "cta_native_http_entry.py":
            selected = range(min(85, len(lines)))
        else:
            selected = [
                i for i, line in enumerate(lines)
                if any(x in line for x in (
                    "Settings(", "api_types=",
                    "CTANative", "register",
                    "create_app", "TestClient",
                    "uvicorn", "run("
                ))
            ]

        for i in selected:
            print(f"{i+1}: {lines[i]}")

print("\n=== CURRENT STAGED LAUNCHER ===")
launcher = stage / "cta_native_launcher.py"
assert launcher.is_file()
lines = launcher.read_text().splitlines()

for i, line in enumerate(lines[:55], 1):
    print(f"{i}: {line}")

print("\nWORKING SERVER COMPARISON: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
print("NO FILES MODIFIED")
print("NO SERVER STARTED")
PY
