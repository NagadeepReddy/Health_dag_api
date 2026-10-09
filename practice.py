python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/grecbase_max.py")
s = p.read_text()

# Add full ContextHead import.
if "from cta_max.context_head_full import ContextHeadFullMAX" not in s:
    s = s.replace(
        "from max.nn import Embedding",
        "from max.nn import Embedding\nfrom cta_max.context_head_full import ContextHeadFullMAX"
    )

# Add ContextHead module after the existing item_pre_embedding block.
needle = '''        self.item_pre_embedding = Embedding(
            vocab_size=10727,
            hidden_dim=112,
            dtype=dtype,
            device=device,
            name="item_pre_embedding",
        )'''

replacement = needle + '''

        # Integrated ContextHead:
        # proven deep path + proven wide path.
        self.context_head = ContextHeadFullMAX(
            dtype=dtype,
            device=device,
        )'''

if needle not in s:
    raise SystemExit("Expected item_pre_embedding block not found - no changes made")

if "self.context_head = ContextHeadFullMAX" not in s:
    s = s.replace(needle, replacement)

p.write_text(s)
print("GRECBASE CONTEXTHEAD INTEGRATED")
PY
