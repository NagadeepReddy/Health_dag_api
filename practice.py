
cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage run --rm -i \
--network none \
--security-opt label=disable \
-v "$PWD:/workspace:ro" \
-w /workspace \
-e PYTHONPATH="/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472-max/pzaas_max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils" \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local - <<'PY'
import importlib
import inspect
import traceback

print("=== PZAAS REAL MAX BRIDGE RUNTIME ===", flush=True)

try:
    import max
    print("MAX RUNTIME: PASS", flush=True)

    module = importlib.import_module(
        "pzaas_max_model_adapter"
    )
    print("PZAAS BRIDGE IMPORT: PASS", flush=True)

    cls = getattr(module, "PZAASMAXModel")
    print("MODEL CLASS: FOUND", flush=True)

    signature = inspect.signature(cls)
    required = [
        p.name for p in signature.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]

    if required:
        print("MODEL CONSTRUCTOR:", signature)
        raise RuntimeError(
            "Constructor requires arguments: "
            + ", ".join(required)
        )

    print("INITIALIZING REAL MAX BRIDGE...", flush=True)
    model = cls()

    print("PZAAS BRIDGE INITIALIZATION: PASS", flush=True)
    print("CALLABLE:", callable(model), flush=True)

    print("NEXT: NATIVE WORKER AND HTTP VALIDATION")

except Exception:
    print("RUNTIME VALIDATION: BLOCKED", flush=True)
    traceback.print_exc()
    raise SystemExit(1)

finally:
    print("ORIGINAL DS: UNCHANGED", flush=True)
    print("CTA / BPLAN: UNCHANGED", flush=True)
    print("SOURCE FILES MODIFIED: NONE", flush=True)
PY
