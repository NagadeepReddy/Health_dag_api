echo "=== NVIDIA GPU DETECTION ==="

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version \
    --format=csv,noheader
else
  echo "NVIDIA-SMI: NOT INSTALLED"
fi

echo "=== NVIDIA DEVICE ACCESS ==="
for d in /dev/nvidia0 /dev/nvidiactl /dev/nvidia-uvm; do
  if [ -e "$d" ]; then
    ls -l "$d"
  else
    echo "$d: NOT PRESENT"
  fi
done

echo "=== NVIDIA PCI DEVICES ==="
if command -v lspci >/dev/null 2>&1; then
  lspci | grep -Ei 'NVIDIA|3D controller' || true
else
  echo "LSPCI: NOT INSTALLED"
fi

echo "GPU READINESS CHECK COMPLETE"
echo "NO FILES MODIFIED"
