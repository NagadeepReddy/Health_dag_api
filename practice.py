sed -i '83c\max_out = out.to_numpy()' artifacts/v1.168-max/cta_max/run_transformer_max.py

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && echo "MAX to_numpy FIX CLEAN"
