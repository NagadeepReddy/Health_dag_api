nl -ba artifacts/v1.168-max/cta_max/run_transformer_max.py | sed -n '1,75p'; \
echo "===== TRANSFORMER BLOCK ====="; \
nl -ba artifacts/v1.168-max/cta_max/parallel_transformer_block.py | sed -n '1,120p'
