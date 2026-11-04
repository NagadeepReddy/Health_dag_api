cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== EXISTING PYTORCH RUNTIME CHECK ==="
found=0

while IFS= read -r id; do
  [ -n "$id" ] || continue

  if "${P[@]}" exec "$id" sh -c '
    for py in /opt/venv/bin/python /opt/venv/bin/python3 /usr/local/bin/python /usr/bin/python3; do
      if [ -x "$py" ] && "$py" -c "import torch" >/dev/null 2>&1; then
        echo "PYTHON: $py"
        "$py" -c "import torch; print(\"TORCH:\", torch.__version__)"
        if [ -d /application1/sajjna8/rt-pzaas-v1.0 ]; then
          echo "PZAAS DIRECTORY: ACCESSIBLE"
        else
          echo "PZAAS DIRECTORY: NOT MOUNTED"
        fi
        exit 0
      fi
    done
    exit 1
  '; then
    echo "CONTAINER ID: $id"
    found=1
  fi
done < <("${P[@]}" ps --format '{{.ID}}')

if [ "$found" -eq 0 ]; then
  echo "NO RUNNING CONTAINER WITH PYTORCH FOUND"
  echo "AVAILABLE LOCAL IMAGES:"
  "${P[@]}" images --format '{{.Repository}}:{{.Tag}}'
fi

echo "ORIGINAL DS: UNCHANGED"
echo "CTA / BPLAN: UNCHANGED"
SH
