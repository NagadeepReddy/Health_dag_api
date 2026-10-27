for f in /application1/podman/storage/overlay/*/diff/opt/venv/lib/python*/site-packages/max/pipelines/architectures/llama3_arch.py; do
  if [ -f "$f" ]; then
    echo "FOUND: $f"
    grep -nE 'llama_arch|weights|encoding|quantization' "$f" | head -30
    break
  fi
done
