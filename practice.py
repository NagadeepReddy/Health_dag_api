cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== LAST MEANINGFUL CTA OUTPUT ===" && \
grep -v 'CTA WORKER RESPONSE IDS: \[\]' \
/application1/cta_env_e2e_1028.log | tail -65
