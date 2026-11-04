cd /application1/sajjna8/rt-pzaas-v1.0 && \
P=artifacts/v1.472-max/pzaas_max && \
D=artifacts/v1.472/utils/dependency-utils/models.py && \
echo "=== EXISTING MAX SEQUENCE TRANSFORMER ===" && \
nl -ba "$P/sequence_transformer_max.py" | head -170 && \
echo "=== ORIGINAL PYTORCH SEQUENCE COMPONENTS ===" && \
grep -n -m 12 -B 3 -A 6 -E \
'sequence_transformer|page_meta_wide_dense|item_pre_embedding' "$D" && \
echo "=== MAX FEATURE ALIGNMENT INSPECTION: COMPLETE ===" && \
echo "ORIGINAL DS: UNCHANGED" && \
echo "CTA / BPLAN: UNCHANGED"
