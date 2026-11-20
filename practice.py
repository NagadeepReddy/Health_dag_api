cd /application1/sajjna8/tfy_triton_work

cat > aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1/model.py <<'EOF'
import json
import os
import sys
from pathlib import Path

import numpy as np
import triton_python_backend_utils as pb_utils


class TritonPythonModel:

    def initialize(self, args):
        config = json.loads(args["model_config"])
        params = config.get("parameters", {})

        self.model_name = params["modelName"]["string_value"]
        self.model_version = params["modelVersion"]["string_value"]

        os.environ["modelName"] = self.model_name
        os.environ["modelVersion"] = self.model_version

        root = Path(__file__).resolve().parent
        sys.path.insert(0, str(root / "core-artifact"))
        sys.path.insert(0, str(root / "utils" / "dependency-utils"))

        from pipeline import pipeline
        self.pipeline = pipeline()
        self.pipeline.load()

    def execute(self, requests):
        responses = []

        for request in requests:
            try:
                tensor = pb_utils.get_input_tensor_by_name(
                    request, "input_request"
                )
                raw = tensor.as_numpy().reshape(-1)[0]

                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")

                payload = json.loads(raw)
                result = self.pipeline.predict_raw(payload)

                response = {
                    "jsonData": {
                        "prediction": result["jsonData"]["prediction"]
                    },
                    "modelDetails": {
                        "modelName": self.model_name,
                        "modelVersion": self.model_version
                    },
                    "transactionMetadata": result.get(
                        "transactionMetadata", {}
                    )
                }

                encoded = json.dumps(response).encode("utf-8")
                output = pb_utils.Tensor(
                    "output_response",
                    np.array([encoded], dtype=object)
                )

                responses.append(
                    pb_utils.InferenceResponse(
                        output_tensors=[output]
                    )
                )

            except Exception as exc:
                responses.append(
                    pb_utils.InferenceResponse(
                        error=pb_utils.TritonError(str(exc))
                    )
                )

        return responses
EOF

python3 -m py_compile aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1/model.py
echo "ADAPTER SYNTAX CHECK COMPLETE"
