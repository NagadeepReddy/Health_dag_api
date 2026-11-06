
cd /application1/sajjna8 && bash <<'SH'
set -euo pipefail

ROOT="/application1/sajjna8/max_shared_infra"
PKG="$ROOT/python/max_runtime_shared"
TEST="$ROOT/tests/test_typed_queue.py"

test -f "$ROOT/bin/run_max_model.sh" || {
  echo "STOP: Shared launcher missing"
  exit 1
}

if [ -e "$PKG" ] || [ -e "$TEST" ]; then
  echo "STOP: Shared queue files already exist; nothing overwritten"
  exit 1
fi

mkdir -p "$PKG" "$ROOT/tests"

cat > "$PKG/__init__.py" <<'PY'
"""Model-independent Modular MAX serving helpers."""
PY

cat > "$PKG/typed_queue.py" <<'PY'
"""Typed MAX Serve response queues, independent of model architecture."""

from typing import Any


def configure_typed_response_queue(
    *,
    scheduler_configs_class,
    zmq_config_class,
    request_id_type,
    scheduler_result_type,
    serializable_output_type,
    owner,
):
    """
    Install a typed queue for one explicitly selected model.

    This changes the scheduler class only when called.
    Repeated registration for the same model is idempotent.
    A conflicting registration raises an error.
    """
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("A nonempty model owner is required")

    if serializable_output_type is None:
        raise ValueError("Serializable output type is required")

    current = scheduler_configs_class.__dict__.get(
        "_max_shared_queue_install"
    )

    if current is not None:
        if current == (owner, serializable_output_type):
            return False
        raise RuntimeError(
            "Scheduler already configured for another response type"
        )

    # Do not silently wrap a model's previous queue monkeypatch.
    legacy = [
        name
        for name, value in vars(scheduler_configs_class).items()
        if name.endswith("_typed_response") and value is True
    ]
    if legacy:
        raise RuntimeError(
            "Existing model-specific queue patch detected: "
            + ", ".join(legacy)
        )

    original_init = scheduler_configs_class.__init__

    response_type = dict[
        request_id_type,
        scheduler_result_type[serializable_output_type],
    ]

    def shared_queue_init(self, pipeline_task):
        original_init(self, pipeline_task)
        self.request_queue_config = zmq_config_class[Any](Any)
        self.response_queue_config = (
            zmq_config_class[response_type](response_type)
        )

    scheduler_configs_class.__init__ = shared_queue_init
    scheduler_configs_class._max_shared_queue_install = (
        owner,
        serializable_output_type,
    )

    return True


def install_max_typed_response_queue(
    serializable_output_type,
    *,
    owner,
):
    """Call explicitly inside a compatible MAX Serve model process."""
    from max.serve.scheduler.queues import SchedulerZmqConfigs
    from max.serve.queue.zmq_queue import ZmqConfig
    from max.interfaces.request import RequestID
    from max.interfaces.scheduler import SchedulerResult

    return configure_typed_response_queue(
        scheduler_configs_class=SchedulerZmqConfigs,
        zmq_config_class=ZmqConfig,
        request_id_type=RequestID,
        scheduler_result_type=SchedulerResult,
        serializable_output_type=serializable_output_type,
        owner=owner,
    )
PY

cat > "$TEST" <<'PY'
import unittest
from typing import Any, Generic, TypeVar

from max_runtime_shared.typed_queue import (
    configure_typed_response_queue,
)

T = TypeVar("T")


class FakeResult(Generic[T]):
    pass


class FakeRequestID:
    pass


class FakeOutput:
    pass


class FakeZmqConfig:
    def __class_getitem__(cls, item):
        return cls

    def __init__(self, item):
        self.item = item


def make_scheduler():
    class Scheduler:
        def __init__(self, pipeline_task):
            self.pipeline_task = pipeline_task
            self.initialized = True

    return Scheduler


def install(scheduler, owner="model_a", output=FakeOutput):
    return configure_typed_response_queue(
        scheduler_configs_class=scheduler,
        zmq_config_class=FakeZmqConfig,
        request_id_type=FakeRequestID,
        scheduler_result_type=FakeResult,
        serializable_output_type=output,
        owner=owner,
    )


class SharedQueueTests(unittest.TestCase):
    def test_typed_queue_installed(self):
        scheduler = make_scheduler()
        self.assertTrue(install(scheduler))

        instance = scheduler("pipeline_task")

        self.assertTrue(instance.initialized)
        self.assertEqual(instance.pipeline_task, "pipeline_task")
        self.assertIs(instance.request_queue_config.item, Any)

        expected = dict[FakeRequestID, FakeResult[FakeOutput]]
        self.assertEqual(instance.response_queue_config.item, expected)

    def test_same_model_is_idempotent(self):
        scheduler = make_scheduler()
        self.assertTrue(install(scheduler))
        previous_init = scheduler.__init__

        self.assertFalse(install(scheduler))
        self.assertIs(scheduler.__init__, previous_init)

    def test_different_model_cannot_override(self):
        scheduler = make_scheduler()
        install(scheduler)

        with self.assertRaises(RuntimeError):
            install(scheduler, owner="model_b")

    def test_legacy_patch_is_preserved(self):
        scheduler = make_scheduler()
        original_init = scheduler.__init__
        scheduler._legacy_typed_response = True

        with self.assertRaises(RuntimeError):
            install(scheduler)

        self.assertIs(scheduler.__init__, original_init)

    def test_invalid_owner_rejected(self):
        scheduler = make_scheduler()

        with self.assertRaises(ValueError):
            install(scheduler, owner="")


if __name__ == "__main__":
    unittest.main()
PY

python3 -m py_compile "$PKG/typed_queue.py" "$TEST"

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$ROOT/python" \
python3 -m unittest discover \
  -s "$ROOT/tests" \
  -p "test_typed_queue.py" \
  -v

echo
echo "=== SHARED MAX INFRA STATUS ==="
echo "SHARED QUEUE MODULE: CREATED"
echo "MODEL RESPONSE TYPE: CONFIGURABLE"
echo "CONFLICT PROTECTION: IMPLEMENTED"
echo "MODEL-SPECIFIC IMPORTS: NONE"
echo "ORIGINAL CTA / BPLAN / PZAAS: UNCHANGED"
echo "RUNNING CONTAINERS: UNCHANGED"
echo "NEXT: SHARED SCHEDULER DESIGN"
SH
