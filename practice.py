R=/application1/cta_max_native_release_candidate_20261028

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 512m --pids-limit 32 \
  -v "$R:/release:ro" \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -S -B - <<'PY'
import ast
from pathlib import Path

files = {
    "MAX RESPONSE RECEIVER":
        Path("/opt/venv/lib/python3.12/site-packages/max/serve/scheduler/queues.py"),
    "CTA HTTP ROUTER":
        Path("/release/cta_router.py"),
    "CTA RESPONSE BRIDGE":
        Path("/release/cta_http_pipeline.py"),
}

for title, path in files.items():
    print(f"\n=== {title} ===")
    assert path.is_file(), f"STOP: Missing {path}"
    lines = path.read_text().splitlines()
    tree = ast.parse("\n".join(lines))

    targets = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.name in ("response_worker", "open_channel", "cta_infer")
                or "response_worker" in node.name
            ):
                targets.append(node)

    if targets:
        for node in targets:
            print(f"\nFUNCTION: {node.name}")
            for i in range(node.lineno, min(node.end_lineno, node.lineno + 115) + 1):
                print(f"{i}: {lines[i-1]}")
    else:
        print("No matching functions")

print("\nFILES MODIFIED: NONE")
print("MAX MODEL STARTUP: NOT PERFORMED")
PY
