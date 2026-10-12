podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
from max.graph import ops

assert hasattr(ops, "relu"), "STOP: relu unavailable"
assert hasattr(ops, "concat"), "STOP: concat unavailable"

p = Path("artifacts/v1.168-max/cta_max/sequence_transformer_max.py")
s = p.read_text()

old_pre = "item_pre = self.item_pre_embedding(item_pre_in)"
old_return = "return page, item, item_meta, item_pre, page_wide"

assert s.count(old_pre) == 1, "STOP: pre-embedding differs"
assert s.count(old_return) == 1, "STOP: return differs"

new_return = """from max.graph import ops

        # Exact LeakyReLU slope 0.2
        page_wide = (
            ops.relu(page_wide)
            - 0.2 * ops.relu(-page_wide)
        )

        # Original base feature order
        page_full = ops.concat(
            [page, page_wide], axis=2
        )
        item_full = ops.concat(
            [item, item_meta, item_pre], axis=2
        )

        # Original element-wise combination
        return page_full * item_full"""

updated = s.replace(
    old_pre,
    "item_pre = self.item_pre_embedding(item_in)",
    1
).replace(old_return, new_return, 1)

ast.parse(updated)
p.write_text(updated)

print("BASE SEQUENCE ASSEMBLY UPDATED")
print("LEAKY RELU 0.2 IMPLEMENTED")
print("ORIGINAL FEATURE ORDER PRESERVED")
print("SYNTAX PASS")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
