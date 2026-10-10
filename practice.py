python - <<'PY'
import numpy as np, os

B="artifacts/v1.168-max/cta_max"

pairs = [
    ("NORM2", "transformer_exact_norm2.npy", "transformer_max_norm2.npy"),
    ("SWIGLU", "transformer_exact_swiglu.npy", "transformer_max_swiglu.npy"),
    ("FF_OUT", "transformer_exact_ff_out.npy", "transformer_max_ff_out.npy"),
]

for name, pt, mx in pairs:
    p=os.path.join(B,pt)
    m=os.path.join(B,mx)
    if os.path.exists(p) and os.path.exists(m):
        a=np.load(p); b=np.load(m)
        print(name, "PT",a.shape,"MAX",b.shape,
              "DIFF",float(np.max(np.abs(a-b))),
              "MATCH",np.allclose(a,b,rtol=1e-4,atol=1e-5))
    else:
        print(name,"MISSING:",pt if not os.path.exists(p) else mx)
PY
