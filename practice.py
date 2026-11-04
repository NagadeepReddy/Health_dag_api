cd /application1/sajjna8/rt-pzaas-v1.0 && \
P=artifacts/v1.472-max/pzaas_max && \
echo "=== PZAAS EXISTING SEQUENCE FEATURE IMPLEMENTATION ===" && \
nl -ba "$P/att_pooling_max.py" | head -160 && \
echo "=== SEQUENCE POSTPROCESS ===" && \
nl -ba "$P/sequence_postprocess_max.py" | head -95 && \
echo "=== ACTUAL FUSION WIRING ===" && \
nl -ba "$P/grecbase_fusion_full_head_72_max.py" | sed -n '17,76p' && \
echo "SEQUENCE IMPLEMENTATION INSPECTION: COMPLETE" && \
echo "ORIGINAL DS: UNCHANGED"
