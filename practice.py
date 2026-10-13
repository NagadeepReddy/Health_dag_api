cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== ORIGINAL PYTORCH SEQUENCE ==="
sed -n '1290,1322p' \
  artifacts/v1.168/utils/dependency-utils/models.py

echo "=== ACTUAL MAX SEQUENCE ==="
sed -n '15,44p' \
  artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py
