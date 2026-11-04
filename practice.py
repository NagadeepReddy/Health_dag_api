cd /application1/sajjna8/rt-pzaas-v1.0 || exit 1

echo "=== PZAAS VALIDATION PATH RESOLUTION ==="

echo "=== HOST VALIDATION DIRECTORIES ==="
for d in \
  /validation \
  /application1/validation \
  "$PWD/validation" \
  "$PWD/artifacts/v1.472-max/validation" \
  "$PWD/artifacts/v1.472-max/pzaas_max/validation"
do
  if [ -d "$d" ]; then
    echo "FOUND: $d"
    ls -lah "$d" | head -25
  fi
done

echo "=== SAVED PYTORCH AND PARITY FILES ==="

find /application1 \
  -path /application1/podman -prune -o \
  -type f \( \
    -name 'ppa_pytorch_reference_01.pt' -o \
    -name '*pytorch_reference*.pt' -o \
    -name '*branch*target*.npz' -o \
    -name '*sequence*target*.npy' -o \
    -name '*sequence*max.npy' \
  \) -print 2>/dev/null

echo "=== VALIDATION PATH RESOLUTION COMPLETE ==="
echo "ORIGINAL DS: UNCHANGED"
echo "CTA / BPLAN: UNCHANGED"
