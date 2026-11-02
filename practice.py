REPO=/application1/sajjna8/rt-pzai-bplan-v1
DEV="$REPO/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev"

mkdir -p "$DEV"

cat > "$DEV/bplan_max_model_adapter.py" <<'PY'
"""BPLAN-only Modular MAX inference adapter. Original DS code unchanged."""

import sys
import types
from pathlib import Path

import numpy as np
import torch


class BPlanMAXModel:
    def __init__(self):
        from max.driver import CPU
        from max.dtype import DType
        from max.graph import DeviceRef, Graph, TensorType
        from max.engine import InferenceSession
        from max.nn import Linear

        self.root = Path(__file__).resolve().parent
        self.device = CPU()
        device_ref = DeviceRef.from_device(self.device)

        # Temporary compatibility for existing isolated MAX graph modules.
        # Does not load CTA model weights or CTA DS code.
        pkg = types.ModuleType("cta_max")
        pkg.__path__ = [str(self.root)]
        sys.modules["cta_max"] = pkg
        sys.path.insert(0, str(self.root))

        from grecbase_fusion_full_head_72_max import (
            build_grecbase_fusion_graph_order_correct
        )
        from run_real_sanity_input_adapter import build_real_inputs

        self.build_inputs = build_real_inputs
        self.session = InferenceSession(devices=[self.device])

        graph = build_grecbase_fusion_graph_order_correct(device_ref)
        assert len(graph.inputs) == 72
        self.graph_inputs = graph.inputs

        checkpoint_root = self.root.parents[1] / "v1.113" / "core-artifact"
        # Resolve from the BPLAN repository rather than CTA.
        checkpoint_root = self.root.parents[3] / "v1.113" / "core-artifact"
        assert (checkpoint_root / "base_model.pt").is_file()
        assert (checkpoint_root / "bplan_model.pt").is_file()

        state = torch.load(
            checkpoint_root / "base_model.pt",
            map_location="cpu",
            weights_only=True,
        )
        if "state_dict" in state:
            state = state["state_dict"]

        registry = {}

        def register(name, value):
            if name in registry:
                assert np.array_equal(registry[name], value), name
            else:
                registry[name] = value

        for name, tensor in state.items():
            if not isinstance(tensor, torch.Tensor):
                continue
            value = tensor.detach().cpu().contiguous().numpy()
            register(name, value)

            if name.endswith(".weight"):
                register(name[:-7], value)

            if (
                name.startswith("sequence_transformer.ptransformer.")
                and ".fn." in name
            ):
                alias = name.replace(".fn.", ".", 1)
                register(alias, value)
                if alias.endswith(".weight"):
                    register(alias[:-7], value)

        self.base = self.session.load(
            graph, weights_registry=registry
        )

        transfer = torch.load(
            checkpoint_root / "bplan_model.pt",
            map_location="cpu",
            weights_only=True,
        )
        if "state_dict" in transfer:
            transfer = transfer["state_dict"]

        weight = (
            transfer["dense1.weight"]
            .detach().cpu().float().numpy()
        )
        assert weight.shape == (10438, 2048)

        head_graph = Graph(
            "bplan_prediction_head",
            input_types=[
                TensorType(DType.float32, [1, 2048], device=device_ref)
            ],
        )

        with head_graph:
            head = Linear(
                in_dim=2048,
                out_dim=10438,
                dtype=DType.float32,
                device=device_ref,
                has_bias=False,
                name="bplan_prediction_head",
            )
            head_graph.output(head(head_graph.inputs[0]))

        self.head = self.session.load(
            head_graph,
            weights_registry={
                "bplan_prediction_head.weight": weight
            },
        )

    def __call__(self, **model_inputs):
        from max.driver import Tensor

        labels, arrays = self.build_inputs(model_in=model_inputs)
        assert len(labels) == len(arrays) == len(self.graph_inputs) == 72

        runtime_inputs = []

        for label, arr, graph_input in zip(
            labels, arrays, self.graph_inputs
        ):
            value = np.asarray(arr)
            expected = np.dtype(
                str(graph_input.type.dtype).split(".")[-1]
            )
            expected_shape = tuple(
                int(d) for d in graph_input.type.shape
            )

            assert value.shape == expected_shape, label

            if value.dtype != expected:
                assert value.dtype == np.int64
                assert expected == np.dtype("float32")
                converted = value.astype(np.float32)
                assert np.array_equal(
                    value, converted.astype(np.int64)
                ), label
                value = converted

            runtime_inputs.append(
                Tensor.from_numpy(np.ascontiguousarray(value))
            )

        base_output = np.asarray(
            self.base.execute(*runtime_inputs)[0].to_numpy(),
            dtype=np.float32,
        )
        assert base_output.shape == (1, 2048)

        scores = np.asarray(
            self.head.execute(
                Tensor.from_numpy(
                    np.ascontiguousarray(base_output)
                )
            )[0].to_numpy(),
            dtype=np.float32,
        )

        assert scores.shape == (1, 10438)
        assert np.isfinite(scores).all()

        # Compatible with original inference(): out.numpy()[0]
        return torch.from_numpy(scores)
PY

python3 -m py_compile "$DEV/bplan_max_model_adapter.py" && \
echo "BPLAN ISOLATED MAX ADAPTER: CREATED" && \
echo "ORIGINAL DS AND CTA: UNCHANGED"
