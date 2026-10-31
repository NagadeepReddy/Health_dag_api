CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030

echo "=== ROTARY WEIGHT LOOKUP ==="
nl -ba "$CLEAN/artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py" | sed -n '35,85p'

echo "=== CLEAN ROTARY WEIGHT FILE ==="
ls -lh "$CLEAN/artifacts/v1.168-max/cta_max/sequence_weights/"*rotary*
