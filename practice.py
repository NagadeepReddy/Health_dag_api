python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

insert = '''

def rotate_half_max(x: TensorValue) -> TensorValue:
    """MAX equivalent of CTA rotate_half()."""
    half = x.shape[-1] // 2
    x1 = x[..., :half]
    x2 = x[..., half:]
    return ops.concat([-x2, x1], axis=-1)


def apply_rotary_pos_emb_max(
    pos: TensorValue,
    x: TensorValue,
) -> TensorValue:
    """Exact CTA rotary equation."""
    return (x * ops.cos(pos)) + (rotate_half_max(x) * ops.sin(pos))

'''

s=s.replace(
    "class ParallelTransformerBlockMAX(Module):",
    insert + "\nclass ParallelTransformerBlockMAX(Module):"
)

# Ensure ops is imported.
s=s.replace(
    "from max.graph import DeviceRef, TensorValue",
    "from max.graph import DeviceRef, TensorValue, ops"
)

with open(p,"w") as f:
    f.write(s)

print("MAX ROTARY HELPERS ADDED")
PY
