echo "=== FIND TRITON IMPLEMENTATION ==="

ROOTS=(/application1)
[ -d /application ] && ROOTS+=(/application)

find "${ROOTS[@]}" -maxdepth 8 \
  \( -name podman -o -name .git -o -name __pycache__ \
     -name node_modules -o -name venv -o \
     -name '.venv' -o -name 'CTA_MAX_*' \
     -name rt-pzaas-cta-offers-v1 \) -prune -o \
  \( -iname '*triton*' \
     -o -iname '*model_repository*' \
     -o -name config.pbtxt \
     -o -iname '*tritonserver*' \) \
  -print 2>/dev/null | head -80

echo "TRITON SEARCH COMPLETE"
