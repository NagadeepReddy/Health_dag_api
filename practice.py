
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_context.py")

code = '''
from max.interfaces.context import BaseContext, GenerationStatus


class CTAContext(BaseContext):
    """Native MAX Serve request context carrying real CTA JSON."""

    def __init__(self, request_id, body):
        if not isinstance(body, dict):
            raise TypeError("CTA request must be a JSON object")
        self._request_id = request_id
        self.body = body
        self._status = GenerationStatus.ACTIVE

    @property
    def request_id(self):
        return self._request_id

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
'''

ast.parse(code)
with p.open("x") as f:
    f.write(code)

print("CTA NATIVE REQUEST CONTEXT CREATED — SYNTAX PASS")
print("Original DS and MAX inference files unchanged")
PY
