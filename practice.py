cd /application1 || exit 1

BUNDLE=CTA_MAX_SRIRAM_HANDOFF_20261028.tar
BACKUP=cta_max_native_http_pass_20261028.tar.gz
EVIDENCE=cta_native_bridge_validation.log
HANDOFF=CTA_MAX_HANDOFF_20261028.txt

if [ -e "$BUNDLE" ]; then
  echo "STOP: Handoff package already exists"
elif [ ! -f "$BACKUP" ] || [ ! -f "$EVIDENCE" ] || [ ! -f "$HANDOFF" ]; then
  echo "STOP: Required handoff file missing"
elif ! sha256sum -c "${BACKUP}.sha256"; then
  echo "STOP: Working integration backup checksum failed"
else
  NEED=$(du -cb "$BACKUP" "$EVIDENCE" "$HANDOFF" | tail -1 | awk '{print $1}')
  FREE=$(df -B1 --output=avail /application1 | tail -1)

  if [ "$FREE" -lt $((NEED * 2 + 1073741824)) ]; then
    echo "STOP: Insufficient safe disk capacity"
  else
    tar -cf "$BUNDLE" \
      "$BACKUP" "${BACKUP}.sha256" \
      "$EVIDENCE" "$HANDOFF" && \
    tar -tf "$BUNDLE" && \
    sha256sum "$BUNDLE" > "${BUNDLE}.sha256" && \
    echo "SRIRAM HANDOFF PACKAGE: PASS"
  fi
fi

echo "DS CODE: UNCHANGED"
echo "CONTAINERS: NOT STARTED"
