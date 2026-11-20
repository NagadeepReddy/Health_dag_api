cd /application1/sajjna8/tfy_triton_work/rt-aal-upg-lead-v1

grep -RniE \
  --include='*.py' --include='*.md' --include='*.sh' \
  'sanity_output|load_input_[123]' . | head -30
