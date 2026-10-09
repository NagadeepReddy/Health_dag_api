sed -i '/^[[:space:]]*shape=\[256\],[[:space:]]*$/d' \
  artifacts/v1.168-max/cta_max/parallel_transformer_block.py

echo "FINAL ORPHANED SHAPE REMOVED"
