sed -i '/^[[:space:]]*dtype=dtype,[[:space:]]*$/d' \
  artifacts/v1.168-max/cta_max/parallel_transformer_block.py

echo "FINAL ORPHANED DTYPE REMOVED"
