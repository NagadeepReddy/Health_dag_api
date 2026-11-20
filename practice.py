git ls-tree -r --name-only origin/triton \
  | grep -E 'config\.pbtxt|model\.py|Dockerfile\.triton'
