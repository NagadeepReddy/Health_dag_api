
cd /application1/sajjna8/rt-pzaas-v1.0 && \
bash <<'SH'
set -u

PODMAN=(podman --root /application1/podman/storage \
--runroot /run/containers/storage)

echo "=== PZAAS OFFLINE APSCHEDULER RECOVERY ==="

found=0
while IFS= read -r img; do
  case "$img" in
    ""|"<none>:<none>") continue ;;
  esac

  echo "CHECKING IMAGE: $img"

  if "${PODMAN[@]}" run --rm --pull=never \
    --network=none \
    --entrypoint /bin/sh "$img" -c '
    for py in /opt/venv/bin/python \
              /usr/local/bin/python3 \
              /usr/bin/python3; do
      if [ -x "$py" ]; then
        "$py" -c "
import importlib.util
raise SystemExit(
    0 if importlib.util.find_spec(
        \"apscheduler\"
    ) else 1
)
" && exit 0
      fi
    done
    exit 1
  ' >/dev/null 2>&1; then
    echo "REAL APSCHEDULER FOUND IN: $img"
    found=1
    break
  fi
done < <("${PODMAN[@]}" images --format '{{.Repository}}:{{.Tag}}')

echo "=== RESULT ==="
if [ "$found" -eq 1 ]; then
  echo "OFFLINE APSCHEDULER SOURCE: FOUND"
  echo "NEXT: REUSE REAL PACKAGE IN ISOLATED PZAAS RUNTIME"
else
  echo "OFFLINE APSCHEDULER SOURCE: NOT FOUND"
  echo "NEXT: OBTAIN APSCHEDULER FROM APPROVED PACKAGE REPOSITORY"
fi
echo "ORIGINAL DS / CTA / BPLAN: UNCHANGED"
SH
