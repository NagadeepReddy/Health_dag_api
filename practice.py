echo "=== ORIGINAL PYTORCH MASK AND ATTENTION ==="
sed -n '560,635p' artifacts/v1.168/utils/dependency-utils/models.py

echo "=== CURRENT MAX ATTENTION ==="
sed -n '75,120p' artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py

echo "=== ACTIVE MAX SEQUENCE CONNECTION ==="
sed -n '16,38p' artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py
