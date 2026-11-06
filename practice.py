
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
PKG="$ROOT/python/max_runtime_shared"
TESTS="$ROOT/tests"

test -f "$PKG/typed_queue.py"
test -f "$PKG/scheduler_hooks.py"

for f in \
  "$PKG/router_contract.py" \
  "$PKG/worker_lifecycle.py" \
  "$TESTS/test_router_contract.py" \
  "$TESTS/test_worker_lifecycle.py"; do
  if [ -e "$f" ]; then
    echo "STOP: File already exists: $f"
    exit 1
  fi
done

echo "=== BUILD SHARED MAX CONTRACTS ==="

cat > "$PKG/router_contract.py" <<'PY'
"""Register model routes on an existing MAX Serve API app."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RouteBinding:
    path: str
    endpoint: Callable
    methods: tuple[str, ...] = ("POST",)

    def __post_init__(self):
        if not isinstance(self.path, str) or not self.path.startswith("/"):
            raise ValueError("Route must begin with /")
        if not callable(self.endpoint):
            raise TypeError("Route endpoint must be callable")
        if not self.methods or any(
            not isinstance(m, str) or not m.isalpha()
            for m in self.methods
        ):
            raise ValueError("Invalid HTTP methods")

        methods = tuple(m.upper() for m in self.methods)
        if len(set(methods)) != len(methods):
            raise ValueError("Duplicate HTTP method")

        object.__setattr__(self, "methods", methods)


def register_model_routes(app, bindings):
    """
    Add routes to an existing MAX Serve app.

    Does not create a FastAPI server or replace MAX routing.
    Checks collisions before adding any requested route.
    """
    if not hasattr(app, "add_api_route") or not hasattr(app, "routes"):
        raise TypeError("Existing API app is required")

    bindings = tuple(bindings)
    if not all(isinstance(b, RouteBinding) for b in bindings):
        raise TypeError("Expected RouteBinding instances")

    occupied = set()

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or ()
        for method in methods:
            occupied.add((path, method.upper()))

    requested = set()

    for binding in bindings:
        for method in binding.methods:
            key = (binding.path, method)
            if key in occupied or key in requested:
                raise ValueError(
                    f"Route conflict: {binding.path} {method}"
                )
            requested.add(key)

    for binding in bindings:
        app.add_api_route(
            binding.path,
            binding.endpoint,
            methods=list(binding.methods),
        )

    return len(bindings)
PY

cat > "$PKG/worker_lifecycle.py" <<'PY'
"""Model-independent single-worker initialization lifecycle."""

from typing import Callable


class WorkerLifecycle:
    """
    Initialize one model worker through injected callbacks.

    The model controls construction, weight loading, and MAX attachment.
    No model-specific imports or DS modifications are required.

    Startup is single-threaded; concurrency must be handled by
    the serving framework.
    """

    def __init__(
        self,
        *,
        create: Callable,
        load: Callable,
        attach_max: Callable,
    ):
        for name, callback in (
            ("create", create),
            ("load", load),
            ("attach_max", attach_max),
        ):
            if not callable(callback):
                raise TypeError(f"{name} must be callable")

        self._create = create
        self._load = load
        self._attach_max = attach_max
        self._instance = None

    @property
    def ready(self):
        return self._instance is not None

    def start(self):
        if self.ready:
            return self._instance

        instance = self._create()
        if instance is None:
            raise RuntimeError("Worker factory returned None")

        self._load(instance)
        self._attach_max(instance)

        # Mark ready only after all initialization stages succeed.
        self._instance = instance
        return instance

    def get(self):
        if not self.ready:
            raise RuntimeError("Worker not initialized")
        return self._instance
PY

cat > "$TESTS/test_router_contract.py" <<'PY'
import unittest
from types import SimpleNamespace

from max_runtime_shared.router_contract import (
    RouteBinding,
    register_model_routes,
)


def handler():
    return {"ok": True}


class FakeApp:
    def __init__(self):
        self.routes = []

    def add_api_route(self, path, endpoint, methods):
        self.routes.append(
            SimpleNamespace(
                path=path,
                endpoint=endpoint,
                methods=set(methods),
            )
        )


class RouterContractTests(unittest.TestCase):

    def test_single_route(self):
        app = FakeApp()
        count = register_model_routes(
            app, [RouteBinding("/model/predict", handler)]
        )
        self.assertEqual(count, 1)
        self.assertEqual(app.routes[0].path, "/model/predict")

    def test_multiple_models(self):
        app = FakeApp()
        register_model_routes(app, [
            RouteBinding("/model_a/predict", handler),
            RouteBinding("/model_b/predict", handler),
        ])
        self.assertEqual(len(app.routes), 2)

    def test_duplicate_rejected(self):
        app = FakeApp()
        register_model_routes(
            app, [RouteBinding("/predict", handler)]
        )
        with self.assertRaises(ValueError):
            register_model_routes(
                app, [RouteBinding("/predict", handler)]
            )
        self.assertEqual(len(app.routes), 1)

    def test_conflict_checked_before_registration(self):
        app = FakeApp()
        bindings = [
            RouteBinding("/same", handler),
            RouteBinding("/same", handler),
        ]
        with self.assertRaises(ValueError):
            register_model_routes(app, bindings)
        self.assertEqual(len(app.routes), 0)

    def test_invalid_endpoint(self):
        with self.assertRaises(TypeError):
            RouteBinding("/predict", None)

    def test_invalid_app(self):
        with self.assertRaises(TypeError):
            register_model_routes(object(), [])


if __name__ == "__main__":
    unittest.main()
PY

cat > "$TESTS/test_worker_lifecycle.py" <<'PY'
import unittest

from max_runtime_shared.worker_lifecycle import WorkerLifecycle


class WorkerLifecycleTests(unittest.TestCase):

    def make_worker(self, events):
        return WorkerLifecycle(
            create=lambda: events.append("create") or {},
            load=lambda obj: events.append("load"),
            attach_max=lambda obj: events.append("attach"),
        )

    def test_initialization_order(self):
        events = []
        worker = self.make_worker(events)
        worker.start()
        self.assertEqual(events, ["create", "load", "attach"])
        self.assertTrue(worker.ready)

    def test_idempotent_start(self):
        events = []
        worker = self.make_worker(events)
        first = worker.start()
        second = worker.start()
        self.assertIs(first, second)
        self.assertEqual(events, ["create", "load", "attach"])

    def test_not_ready_before_start(self):
        worker = self.make_worker([])
        with self.assertRaises(RuntimeError):
            worker.get()

    def test_failed_load_not_ready(self):
        def fail(obj):
            raise RuntimeError("Model load failed")

        worker = WorkerLifecycle(
            create=lambda: {},
            load=fail,
            attach_max=lambda obj: None,
        )

        with self.assertRaises(RuntimeError):
            worker.start()
        self.assertFalse(worker.ready)

    def test_failed_attach_not_ready(self):
        def fail(obj):
            raise RuntimeError("MAX attachment failed")

        worker = WorkerLifecycle(
            create=lambda: {},
            load=lambda obj: None,
            attach_max=fail,
        )

        with self.assertRaises(RuntimeError):
            worker.start()
        self.assertFalse(worker.ready)

    def test_independent_workers(self):
        a = self.make_worker([])
        b = self.make_worker([])

        a.start()

        self.assertTrue(a.ready)
        self.assertFalse(b.ready)


if __name__ == "__main__":
    unittest.main()
PY

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT/python" \
python3 -B -m unittest discover \
  -s "$TESTS" \
  -p 'test_router_contract.py' -v

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT/python" \
python3 -B -m unittest discover \
  -s "$TESTS" \
  -p 'test_worker_lifecycle.py' -v

if id sajjna8 >/dev/null 2>&1; then
  chown sajjna8:"$(id -gn sajjna8)" \
    "$PKG/router_contract.py" \
    "$PKG/worker_lifecycle.py" \
    "$TESTS/test_router_contract.py" \
    "$TESTS/test_worker_lifecycle.py"
fi

echo
echo "=== SHARED MAX INFRASTRUCTURE ==="
echo "GENERIC LAUNCHER: PREVIOUSLY PASSED"
echo "SHARED QUEUE: PREVIOUSLY PASSED"
echo "SHARED SCHEDULER HOOKS: PREVIOUSLY PASSED"
echo "SHARED ROUTER CONTRACT: TESTED"
echo "SHARED WORKER LIFECYCLE: TESTED"
echo "MODEL-SPECIFIC IMPORTS: NONE"
echo "ORIGINAL DS / CTA / BPLAN / PZAAS: UNCHANGED"
echo "NATIVE MAX INTEGRATION: PENDING"
echo "NEXT: REAL MAX RUNTIME COMPATIBILITY"
SH
