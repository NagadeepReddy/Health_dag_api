cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -c 'import json; p="artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"; d=json.load(open(p)); print("TOP-LEVEL:",list(d)); print("transactionMetadata:",d.get("transactionMetadata")); print("jsonData.prediction:",list(d.get("jsonData",{}).get("prediction",{})))'
