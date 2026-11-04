cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

files = {
    "ORIGINAL PYTORCH": (
        Path("artifacts/v1.472/utils/dependency-utils/models.py"),
        [(470,485),(537,563),(630,671)]
    ),
    "MAX ATTENTION": (
        Path("artifacts/v1.472-max/pzaas_max/parallel_transformer_block_2layers.py"),
        [(20,45),(75,143)]
    ),
    "MAX FUSION": (
        Path("artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py"),
        [(27,43)]
    )
}

terms = (
    "scale", "heads", "dim_head", "reshape",
    "permute", "split", "rotary", "norm",
    "mask", "valid", "einsum", "matmul",
    "softmax", "attn", "ff_out", "return",
    "sx1", "sx2", "block0", "block1",
    "q =", "k =", "v =", "out +",
    "out +=", "fused", "residual"
)

print("=== PZAAS EXACT ATTENTION ALIGNMENT ===")

for label, (path, ranges) in files.items():
    print("\n###", label)
    if not path.is_file():
        print("BLOCKED: MISSING", path)
        continue

    lines = path.read_text().splitlines()
    selected = set()

    for start, end in ranges:
        for i in range(start-1, min(end,len(lines))):
            if any(t in lines[i].lower() for t in terms):
                selected.update(range(max(start-1,i-1),
                                      min(end,i+2)))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")

print("\nSOURCE ALIGNMENT INSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: CORRECT VERIFIED ATTENTION DIFFERENCE")
PY
