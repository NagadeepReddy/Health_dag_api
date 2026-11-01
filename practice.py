ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/nlp_bert_max.py"
weights = root / "max_weights"

assert file.is_file(), "STOP: MAX loader missing"
assert (weights / "nlp_encoder.embeddings.word_embeddings.weight.npy").is_file(), "STOP: BPLAN NLP weight missing"

original = file.read_text()
old = 'WEIGHTS = Path(__file__).parent / "nlp_weights"'
new = 'WEIGHTS = Path(__file__).resolve().parent.parent / "max_weights"'

assert original.count(old) == 1, "STOP: unexpected loader configuration"

backup = file.with_suffix(".py.before_bplan_nlp_fix")
assert not backup.exists(), "STOP: backup already exists"

updated = original.replace(old, new)
compile(updated, str(file), "exec")

backup.write_text(original)
file.write_text(updated)

print("BPLAN NLP WEIGHT PATH: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
