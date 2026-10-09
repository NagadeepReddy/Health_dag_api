python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_graph.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''    block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
    )
''',
'''    block = ParallelTransformerBlockMAX(
        dtype=DType.float32,
        device=device_ref,
    )

    # Register all MAX module weights using the same mechanism
    # already validated by ContextHead.
    weights_registry.update(block.weights)
'''
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER WEIGHT REGISTRY WIRED")
PY
