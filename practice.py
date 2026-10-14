python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max")

source = (p / "grecbase_fusion_order_correct_max_branch_diag.py").read_text()
old = "graph.output(result, seq, context, search0, search1, task, jet, ihq, sibling)"
assert old in source, "STOP: graph output differs"
source = source.replace(
    old,
    "graph.output(result, seq, context, search0, search1, task, jet, ihq, sibling, sx, sx1, sx2)"
)
(p / "grecbase_sequence_stage_diag.py").write_text(source)

runner = (p / "run_real_sanity_max_branch_diag.py").read_text()
assert "len(outputs) != 9" in runner, "STOP: output count differs"
runner = runner.replace(
    "cta_max.grecbase_fusion_order_correct_max_branch_diag",
    "cta_max.grecbase_sequence_stage_diag"
).replace("len(outputs) != 9", "len(outputs) != 12")

runner += '''
print("\\n=== MAX SEQUENCE STAGES ===")
stages = {}
for name, output in zip(
    ["features", "after_block0", "after_block1"],
    outputs[9:12]
):
    array = output.to_numpy()
    stages[name] = array
    print(name, array.shape, "MIN:", array.min(),
          "MAX:", array.max(), "MEAN:", array.mean())
np.savez_compressed(BASE / "max_sequence_stages_diag.npz", **stages)
'''
(p / "run_sequence_stage_diag.py").write_text(runner)
print("Diagnostic copies created. Original files unchanged.")
PY
