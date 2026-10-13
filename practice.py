cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

nl -ba artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py | sed -n '30,125p'
