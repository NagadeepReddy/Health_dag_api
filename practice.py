cd /application1 || exit 1

BUNDLE=CTA_MAX_VALIDATED_RELEASE_20261028.tar.gz

if [ -e "$BUNDLE" ] || [ -e "${BUNDLE}.sha256" ]; then
  echo "STOP: Release package already exists"
elif [ ! -d cta_max_native_release_candidate_20261028 ] ||
     [ ! -f cta_native_release_candidate_validation.log ]; then
  echo "STOP: Release files missing"
elif ! grep -q 'RELEASE CANDIDATE RUNTIME: PASS' \
       cta_native_release_candidate_validation.log 2>/dev/null &&
     ! { grep -q 'CTA NATIVE HTTP STATUS: 200' \
          cta_native_release_candidate_validation.log &&
          grep -q 'CTA NATIVE END-TO-END: PASS' \
          cta_native_release_candidate_validation.log; }; then
  echo "STOP: Runtime evidence not confirmed"
elif [ "$(df -B1 --output=avail /application1 | tail -1)" -lt 2147483648 ]; then
  echo "STOP: Insufficient free disk space"
else
  tar -czf "$BUNDLE" \
    cta_max_native_release_candidate_20261028 \
    cta_native_release_candidate_validation.log \
    CTA_MAX_HANDOFF_20261028.txt \
    CTA_MAX_CPU_BASELINE_20261028.txt && \
  tar -tzf "$BUNDLE" >/dev/null && \
  sha256sum "$BUNDLE" > "${BUNDLE}.sha256" && \
  sha256sum -c "${BUNDLE}.sha256" && \
  echo "VALIDATED RELEASE PACKAGE: PASS"
fi

echo "DS CODE: UNCHANGED"
echo "CONTAINERS: NOT STARTED"
