python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p) as f:
    s=f.read()

needle="model = session.load(graph, weights_registry=weights)"

assert needle in s, "Expected session.load line not found"

replacement="""# RMSNorm internally requests the registry key 'weight'.
# Map the real CTA transformer norm1.g checkpoint weight to that key.
weights["weight"] = weights[
    "sequence_transformer.ptransformer.0.fn.norm1.g"
]

model = session.load(graph, weights_registry=weights)"""

s=s.replace(needle, replacement, 1)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER NORM1 WEIGHT REGISTRY MAPPED")
PY
