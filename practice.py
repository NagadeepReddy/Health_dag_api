cd /application1 && \
sha256sum -c CTA_MAX_UPDATED_RELEASE_20261028.tar.gz.sha256 && \
tar -tzf CTA_MAX_UPDATED_RELEASE_20261028.tar.gz >/dev/null && \
echo "UPDATED RELEASE ARCHIVE: VERIFIED — PASS"
