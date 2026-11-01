cd /application1/sajjna8/rt-pzai-bplan-v1 && \
echo "=== IMPORTS ===" && \
sed -n '1,110p' artifacts/v1.113/core-artifact/pipeline.py && \
echo "=== MODEL LOADING ===" && \
sed -n '775,840p' artifacts/v1.113/core-artifact/pipeline.py
