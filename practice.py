sed -i '83,85c\
max_out = out._to_numpy()\
np.save(BASE + "/transformer_max_output.npy", max_out)' artifacts/v1.168-max/cta_max/run_transformer_max.py

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && echo "MAX _to_numpy FIX CLEAN"
