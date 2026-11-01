cd /application1/sajjna8/rt-pzai-bplan-v1 && \
grep -nE '^[[:space:]]*(class |def (predict_raw|preprocess|inference|inference_batch|postprocess|load|loadModel|loadBaseModel|loadTransferModel)\()' \
artifacts/v1.113/core-artifact/pipeline.py
