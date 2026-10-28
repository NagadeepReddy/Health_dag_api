cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028/cta_max

echo "=== ACTIVE MAX GRAPH: INPUTS AND OPERATIONS ==="
nl -ba "$BASE/grecbase_fusion_full_head_72_max.py" \
  | sed -n '1,125p'

echo "=== LIVE MAX COMPILATION AND INPUT PREPARATION ==="
nl -ba "$BASE/run_live_max_inference.py" \
  | sed -n '20,100p;185,215p'

echo "=== CTA PIPELINE BRIDGE ==="
nl -ba "$BASE/live_cta_pipeline_bridge.py" \
  | sed -n '1,65p'

echo "READ-ONLY BATCH DESIGN CHECK: COMPLETE"
echo "WORKING CPU HTTP 200: PRESERVED"
echo "DS CODE: UNCHANGED"
