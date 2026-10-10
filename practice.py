cp artifacts/v1.168-max/cta_max/run_transformer_parity.py \
   artifacts/v1.168-max/cta_max/run_transformer_parity.py.bak && \
python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_parity.py")
s = p.read_text()

needle = "result = pt.load_state_dict(block_state, strict=True)"

hook = r'''
# Capture intermediates from the REAL CTA ParallelTransformerBlock.
_real_intermediates = {}

def _capture(name):
    def hook(module, inputs, output):
        import torch
        value = output
        if isinstance(value, (tuple, list)):
            value = value[0]
        if torch.is_tensor(value):
            _real_intermediates[name] = value.detach().cpu().numpy()
    return hook

pt.norm1.register_forward_hook(_capture("norm1"))
pt.fused_attn_ff_proj.register_forward_hook(_capture("fused"))
pt.norm2.register_forward_hook(_capture("norm2"))
pt.attn_out.register_forward_hook(_capture("attn_out"))
pt.ff_out.register_forward_hook(_capture("ff_out"))
'''

if "_real_intermediates = {}" not in s:
    if needle not in s:
        raise SystemExit("STOP: verified load_state_dict line not found")
    s = s.replace(needle, needle + "\n" + hook, 1)

save_needle = 'np.save(BASE + "/transformer_pytorch_output.npy"'

idx = s.find(save_needle)
if idx == -1:
    raise SystemExit("STOP: existing transformer output save not found")

line_end = s.find("\n", idx)
if line_end == -1:
    line_end = len(s)

save_hooks = r'''

for _name, _value in _real_intermediates.items():
    np.save(BASE + "/transformer_real_" + _name + ".npy", _value)
    print("REAL", _name, _value.shape)

print("REAL BLOCK INTERMEDIATES SAVED")
'''

if "REAL BLOCK INTERMEDIATES SAVED" not in s:
    s = s[:line_end] + save_hooks + s[line_end:]

p.write_text(s)
PY

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_parity.py && \
echo "REAL BLOCK HOOKS ADDED - SYNTAX CLEAN"
