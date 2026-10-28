cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

ARCHIVE=/application1/cta_max_native_http_pass_20261028.tar.gz
CHECKSUM="${ARCHIVE}.sha256"

if [ -e "$ARCHIVE" ] || [ -e "$CHECKSUM" ]; then
  echo "STOP: Backup already exists"
else
  tar -czf "$ARCHIVE" \
    artifacts/v1.168-max/maxserve_cta_extension

  tar -tzf "$ARCHIVE" >/dev/null &&
  sha256sum "$ARCHIVE" | tee "$CHECKSUM" &&
  echo "WORKING MAX INTEGRATION BACKUP: PASS"
fi
