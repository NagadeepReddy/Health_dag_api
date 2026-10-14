{
  echo "=== ORIGINAL PYTORCH MASK ==="
  sed -n '655,685p' artifacts/v1.168/utils/dependency-utils/models.py
  echo "=== CURRENT MAX MASK ==="
  sed -n '102,130p' artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py
}
