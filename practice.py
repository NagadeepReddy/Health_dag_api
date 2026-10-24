cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/maxserve_cta_extension")
src = base / "cta_native_e2e_test.py"
dst = base / "cta_native_live_server.py"

source = src.read_text()
tree = ast.parse(source)

main = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "main"
)

client = next(
    n for n in main.body
    if isinstance(n, ast.With)
    and any(
        isinstance(i.context_expr, ast.Call)
        and isinstance(i.context_expr.func, ast.Name)
        and i.context_expr.func.id == "TestClient"
        for i in n.items
    )
)

head = "".join(source.splitlines(keepends=True)[:client.lineno - 1])

runner = head + '''
    import uvicorn
    print("CTA REAL MAX HTTP SERVER STARTING", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")

if __name__ == "__main__":
    main()
'''

compile(runner, str(dst), "exec")
dst.write_text(runner)
print("CTA LIVE SERVER LAUNCHER: READY")
print("ORIGINAL TEST AND DS CODE: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --name cta-native-live \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py
