sed -i 's/ops\.softmax(scores, axis=-1)/ops.softmax(scores, -1)/' \
artifacts/v1.168-max/cta_max/test_transformer_attention_max.py

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_attention_max.py && \
echo "SOFTMAX ARG FIXED - SYNTAX CLEAN"
