echo "===== WORKING CONTEXTHEAD RMSNORM ====="
nl -ba artifacts/v1.168-max/cta_max/run_context_head_deep.py | sed -n '31,65p'

echo
echo "===== TRANSFORMER RMSNORM ====="
nl -ba artifacts/v1.168-max/cta_max/run_transformer_max.py | sed -n '20,75p'
