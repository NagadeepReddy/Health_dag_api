python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
    "from max.nn import Linear, RMSNorm, Weight",
    "from max.nn import Linear, RMSNorm"
)

# Remove the invalid Weight(...) declaration.
start = s.find("        # Real CTA checkpoint weight: rotary_emb.inv_freq")
end = s.find("\n        # PyTorch checkpoint: (3072, 256)", start)

if start != -1 and end != -1:
    s = s[:start] + s[end:]

with open(p, "w") as f:
    f.write(s)

print("INVALID MAX WEIGHT IMPORT REMOVED")
PY
