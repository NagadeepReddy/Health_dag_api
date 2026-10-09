sed -i '/self\.norm1_g = Weight/d; /self\.norm2_g = Weight/d' artifacts/v1.168-max/cta_max/parallel_transformer_block.py

echo "STALE TRANSFORMER WEIGHT OBJECTS REMOVED"
