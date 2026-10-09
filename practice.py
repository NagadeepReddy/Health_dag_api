python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'''        return q, k, v, ff
''',
'''        # Match original ParallelTransformerBlock head layout.
        # q: [batch, seq, 512] -> [batch, 2, seq, 256]
        # k/v: [batch, seq, 256] -> [batch, 1, seq, 256]
        q = q.reshape([q.shape[0], q.shape[1], 2, 256]).permute([0, 2, 1, 3])
        k = k.reshape([k.shape[0], k.shape[1], 1, 256]).permute([0, 2, 1, 3])
        v = v.reshape([v.shape[0], v.shape[1], 1, 256]).permute([0, 2, 1, 3])

        return q, k, v, ff
'''
)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER QKV HEAD RESHAPE ADDED")
PY
