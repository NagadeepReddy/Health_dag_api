cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -c 'import json; p="artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"; d=json.load(open(p)); print("TOP LEVEL:",list(d)); print("JSONDATA TYPE:",type(d.get("jsonData")).__name__); print("EVENTS TYPE:",type(d.get("Events")).__name__); print("PROFILE TYPE:",type(d.get("profile")).__name__)'
