cd /application1 || exit 1

PKG=/application1/CTA_MAX_VALIDATED_RELEASE_20261028.tar.gz
SRC=/application1/cta_max_native_release_candidate_20261028

if [ ! -s "$PKG" ] || [ ! -d "$SRC" ]; then
  echo "STOP: Validated package or source missing"
else
  echo "=== CODE CHANGES SINCE RELEASE PACKAGE ==="
  find "$SRC" -type f \
    \( -name '*.py' -o -name '*.json' -o -name '*.yaml' \) \
    -newer "$PKG" -print

  echo "=== PACKAGE ==="
  ls -lh "$PKG" "$PKG.sha256"

  echo "CHECK COMPLETE — NO FILES MODIFIED"
  echo "MAX NOT STARTED"
fi
