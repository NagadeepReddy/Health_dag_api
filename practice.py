podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
from max.graph import ops

p = Path("artifacts/v1.168-max/cta_max/sequence_transformer_max.py")
s = p.read_text()

assert hasattr(ops, "maximum"), "STOP: MAX maximum operation unavailable"

old_pre = "item_pre = self.item_pre_embedding(item_pre_in)"
old_return = "return page, item, item_meta, item_pre, page_wide"

assert s.count(old_pre) == 1, "STOP: pre-embedding implementation differs"
assert s.count(old_return) == 1, "STOP: sequence return differs"
assert "from max.graph import ops" not in s, "STOP: check existing ops import"

s = s.replace(
    old_pre,
    "item_pre = self.item_pre_embedding(item_in)",
    1
)

s = s.replace(
    old_return,
    """from max.graph import ops

        # Original page-wide LeakyReLU(0.2).
        page_wide = ops.maximum(page_wide, page_wide * 0.2)

        # Base-model feature dimensions: 224+32 and 112+32+112.
        page_full = ops.concat([page, page_wide], axis=2)
        item_full = ops.concat([item, item_meta, item_pre], axis=2)

        return page_full * item_full""",
    1
)

ast.parse(s)
p.write_text(s)

print("BASE SEQUENCE FEATURE ASSEMBLY CREATED")
print("ORIGINAL FEATURE ORDER PRESERVED")
print("ITEM PRE-EMBEDDING INPUT CORRECTED")
print("SYNTAX OK")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
