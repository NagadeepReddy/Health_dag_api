cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/cta_max_true_batch_dev_20261028/cta_native_benchmark_helper.py")
backup = p.with_name("cta_native_benchmark_helper.py.before_shared_portal.bak")

assert p.is_file(), "STOP: Benchmark helper missing"
assert not backup.exists(), "STOP: Backup already exists"

source = p.read_text()

old = (
    "    with ThreadPoolExecutor(max_workers=2) as executor:\n"
    "        futures = [executor.submit(send, n) for n in (1, 2)]\n"
    "        results = [f.result() for f in futures]"
)

assert source.count(old) == 1, "STOP: Benchmark code differs"

new = (
    "    from anyio.from_thread import start_blocking_portal\n"
    "    from contextlib import nullcontext\n"
    "    assert hasattr(client, 'portal') and hasattr(client, 'async_backend'), 'STOP: Unsupported TestClient'\n"
    "    existing = client.portal\n"
    "    context = nullcontext(existing) if existing is not None else start_blocking_portal(**client.async_backend)\n"
    "    with context as portal:\n"
    "        if existing is None:\n"
    "            client.portal = portal\n"
    "        try:\n"
    "            with ThreadPoolExecutor(max_workers=2) as executor:\n"
    "                futures = [executor.submit(send, n) for n in (1, 2)]\n"
    "                results = [f.result() for f in futures]\n"
    "        finally:\n"
    "            if existing is None:\n"
    "                client.portal = None"
)

updated = source.replace(old, new)
ast.parse(updated)

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("SHARED TESTCLIENT PORTAL: INSTALLED")
print("PYTHON SYNTAX: PASS")
print("BACKUP: CREATED")
print("NATIVE SERVING CODE: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
