timeout 15s find /application1/sajjna8 \
  -type f \( -iname '*faiss*.whl' -o -iname '*faiss*.so' \) \
  -print -quit
