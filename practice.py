
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
PKG="$ROOT/python/max_runtime_shared"
MODULE="$PKG/scheduler_hooks.py"
TEST="$ROOT/tests/test_scheduler_hooks.py"

test -f "$PKG/typed_queue.py" || {
  echo "STOP: Shared queue module missing"
  exit 1
}

if [ -e "$MODULE" ] || [ -e "$TEST" ]; then
  echo "STOP: Scheduler files already exist"
  exit 1
fi

cat > "$MODULE" <<'PY'
"""Model-independent native MAX scheduler hook registration."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SchedulerHooks:
    model_key: str
    install_queue: Callable[[], None]
    install_scheduler: Callable[[], None]

    def __post_init__(self):
        if not isinstance(self.model_key, str) or not self.model_key.strip():
            raise ValueError("A model key is required")

        if not callable(self.install_queue):
            raise TypeError("Queue installer must be callable")

        if not callable(self.install_scheduler):
            raise TypeError("Scheduler installer must be callable")


class SharedSchedulerRegistry:
    """Register independent model scheduler hooks without model imports."""

    def __init__(self):
        self._models = {}
        self._activated = set()

    def register(self, hooks: SchedulerHooks):
        if hooks.model_key in self._models:
            raise ValueError(
                f"Model already registered: {hooks.model_key}"
            )

        self._models[hooks.model_key] = hooks

    def activate(self, model_key: str):
        if model_key not in self._models:
            raise KeyError(f"Unknown model: {model_key}")

        if model_key in self._activated:
            return False

        hooks = self._models[model_key]

        # Preserve existing MAX queue-before-scheduler ordering.
        hooks.install_queue()
        hooks.install_scheduler()

        self._activated.add(model_key)
        return True

    def is_activated(self, model_key: str):
        return model_key in self._activated

    def registered_models(self):
        return tuple(sorted(self._models))
PY

cat > "$TEST" <<'PY'
import unittest

from max_runtime_shared.scheduler_hooks import (
    SchedulerHooks,
    SharedSchedulerRegistry,
)


class SchedulerHookTests(unittest.TestCase):

    def test_registration(self):
        registry = SharedSchedulerRegistry()
        registry.register(
            SchedulerHooks("model_a", lambda: None, lambda: None)
        )
        self.assertEqual(registry.registered_models(), ("model_a",))

    def test_installation_order(self):
        calls = []
        registry = SharedSchedulerRegistry()
        registry.register(SchedulerHooks(
            "model_a",
            lambda: calls.append("queue"),
            lambda: calls.append("scheduler"),
        ))

        self.assertTrue(registry.activate("model_a"))
        self.assertEqual(calls, ["queue", "scheduler"])
        self.assertTrue(registry.is_activated("model_a"))

    def test_idempotent_activation(self):
        calls = []
        registry = SharedSchedulerRegistry()
        registry.register(SchedulerHooks(
            "model_a",
            lambda: calls.append("queue"),
            lambda: calls.append("scheduler"),
        ))

        registry.activate("model_a")
        self.assertFalse(registry.activate("model_a"))
        self.assertEqual(calls, ["queue", "scheduler"])

    def test_duplicate_registration_rejected(self):
        registry = SharedSchedulerRegistry()
        hooks = SchedulerHooks(
            "model_a", lambda: None, lambda: None
        )
        registry.register(hooks)

        with self.assertRaises(ValueError):
            registry.register(hooks)

    def test_models_remain_isolated(self):
        calls = []
        registry = SharedSchedulerRegistry()

        for name in ("model_a", "model_b"):
            registry.register(SchedulerHooks(
                name,
                lambda n=name: calls.append((n, "queue")),
                lambda n=name: calls.append((n, "scheduler")),
            ))

        registry.activate("model_b")

        self.assertEqual(
            calls,
            [("model_b", "queue"), ("model_b", "scheduler")]
        )
        self.assertFalse(registry.is_activated("model_a"))

    def test_failure_does_not_mark_activated(self):
        registry = SharedSchedulerRegistry()

        def fail():
            raise RuntimeError("Scheduler installation failed")

        registry.register(SchedulerHooks(
            "model_a", lambda: None, fail
        ))

        with self.assertRaises(RuntimeError):
            registry.activate("model_a")

        self.assertFalse(registry.is_activated("model_a"))


if __name__ == "__main__":
    unittest.main()
PY

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT/python" \
python3 -B -m unittest discover \
  -s "$ROOT/tests" \
  -p "test_scheduler_hooks.py" \
  -v

if id sajjna8 >/dev/null 2>&1; then
  chown sajjna8:"$(id -gn sajjna8)" "$MODULE" "$TEST"
fi

echo
echo "=== SHARED MAX INFRASTRUCTURE ==="
echo "SHARED QUEUE: PREVIOUSLY PASSED"
echo "SHARED SCHEDULER REGISTRATION: CREATED"
echo "QUEUE-BEFORE-SCHEDULER ORDER: TESTED"
echo "MODEL-SPECIFIC PYTHON IMPORTS: NONE"
echo "NATIVE MAX INTEGRATION: PENDING"
echo "CTA / BPLAN / PZAAS: UNCHANGED"
echo "RUNNING CONTAINERS: UNCHANGED"
echo "NEXT: SHARED ROUTER AND WORKER-LIFECYCLE CONTRACTS"
SH
