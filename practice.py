cd /application1/sajjna8/tfy_triton_work

cat > aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/config.pbtxt <<'EOF'
name: "rt-aal-upg-leads-v1"
backend: "python"
max_batch_size: 0

input [
  {
    name: "input_request"
    data_type: TYPE_STRING
    dims: [1]
  }
]

output [
  {
    name: "output_response"
    data_type: TYPE_STRING
    dims: [1]
  }
]

instance_group [
  {
    count: 1
    kind: KIND_CPU
  }
]

parameters {
  key: "modelName"
  value { string_value: "rt-aal-upg-leads" }
}

parameters {
  key: "modelVersion"
  value { string_value: "v1.4" }
}
EOF

cat aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/config.pbtxt
