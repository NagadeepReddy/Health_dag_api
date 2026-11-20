P=/application1/sajjna8/tfy_triton_work/aal_triton_stage/input/load_input_3.json

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec -i aal-triton-check python3 -c '
import json, sys, urllib.request

sample = json.load(sys.stdin)
request = {
    "inputs": [{
        "name": "input_request",
        "shape": [1],
        "datatype": "BYTES",
        "data": [json.dumps(sample)]
    }],
    "outputs": [{"name": "output_response"}]
}

url = "http://127.0.0.1:8000/v2/models/rt-aal-upg-leads-v1/infer"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
req = urllib.request.Request(
    url,
    data=json.dumps(request).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

response = opener.open(req, timeout=120)
body = json.load(response)
result = json.loads(body["outputs"][0]["data"][0])

print("TRITON HTTP STATUS:", response.status)
print("OUTPUT KEYS:", list(result))
print("PREDICTION:", result.get("jsonData", {}).get("prediction"))
' < "$P"
