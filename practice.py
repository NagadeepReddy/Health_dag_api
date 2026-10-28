cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== MODEL ID REQUIREMENT ===" && \
nl -ba artifacts/v1.168/utils/dependency-utils/utils.py | sed -n '25,38p' && \
echo "=== EXISTING MODEL METADATA ===" && \
nl -ba artifacts/v1.168/core-artifact/pipeline.py | sed -n '3098,3132p'
