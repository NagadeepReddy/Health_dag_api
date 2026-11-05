cd /application1/sajjna8/rt-pzaas-v1.0 && podman --root /application1/podman/storage --runroot /run/containers/storage run --rm -i --pull=never --network=none --security-opt label=disable -v "$PWD:/workspace:ro" -w /workspace --entrypoint python localhost/cta-max-faiss:local - <<'PY'
import sys, json, inspect, re, traceback
from pathlib import Path
import numpy as np
import torch

root = Path('/workspace/artifacts/v1.472')
mx = Path('/workspace/artifacts/v1.472-max')
val = mx / 'pzaas_max/validation'
sys.path[:0] = [
    str(root/'utils/dependency-utils'),
    str(root/'core-artifact'),
    str(mx)
]
torch.set_num_threads(2)

status = {
    'ORIGINAL PYTORCH': 'PENDING',
    '72 INPUTS': 'PENDING',
    'MAX CPU': 'PENDING',
    'LAYER-0': 'PENDING',
    'EIGHT BRANCHES': 'PENDING',
    'FULL MODEL': 'PENDING'
}

try:
    from models import GRecBase
    from max.driver import CPU
    from max.dtype import DType
    from max.engine import InferenceSession
    from max.graph import Graph, TensorType, DeviceRef
    from pzaas_max.grecbase_fusion_full_head_72_max import (
        build_grecbase_fusion_graph_order_correct
    )
    from pzaas_max.parallel_transformer_block_2layers import (
        ParallelTransformerBlockMAX
    )

    def arr(v, typ=None):
        if isinstance(v, torch.Tensor):
            v = v.detach().cpu().numpy()
        return np.ascontiguousarray(np.asarray(v, dtype=typ))

    def scalar(v):
        return arr(v, np.int64).reshape(1)

    params = json.loads(
        (root/'config/torch_model_params_base.json').read_text()
    )
    if isinstance(params, list):
        params = params[0]

    params.update(
        nlp_encoder_path=str(root/'config/config.json'),
        transfer_ind=True,
        extract_deep_idx=-1
    )

    state = torch.load(
        root/'core-artifact/model_0_base.pt',
        map_location='cpu',
        weights_only=False
    )
    if isinstance(state, dict) and 'state_dict' in state:
        state = state['state_dict']

    model = GRecBase(**params)
    model.load_state_dict(state, strict=True)
    model.eval()

    saved = torch.load(
        val/'ppa_model_input_exact.pt',
        map_location='cpu',
        weights_only=False
    )
    data = saved.get('model_in', saved)

    assert 'vl_in' in data and 'sibling_vl_in' in data, \
        'Lowercase-L inputs missing'

    layer = dict(model.named_modules())[
        'sequence_transformer.ptransformer.0'
    ]
    fn = layer.fn
    trace = {}

    hooks = [
        fn.register_forward_pre_hook(
            lambda m, a: trace.update(
                input=a[0].detach().cpu().clone()
            )
        ),
        fn.register_forward_hook(
            lambda m, a, o: trace.update(
                fn=o.detach().cpu().clone()
            )
        ),
        layer.register_forward_hook(
            lambda m, a, o: trace.update(
                residual=o.detach().cpu().clone()
            )
        )
    ]

    aliases = {'tasks_in': 'task_in', 'task_in': 'tasks_in'}
    kwargs = {}

    for key, p in inspect.signature(model.forward).parameters.items():
        if key == 'self':
            continue
        actual = key if key in data else aliases.get(key)
        if actual in data:
            kwargs[key] = data[actual]
        elif p.default is inspect.Parameter.empty:
            raise KeyError('Original input missing: ' + key)

    try:
        with torch.inference_mode():
            original = model(**kwargs)
    finally:
        for h in hooks:
            h.remove()

    if isinstance(original, (tuple, list)):
        original = next(
            (
                v for v in original
                if isinstance(v, torch.Tensor)
                and tuple(v.shape) == (1, 2048)
            ),
            None
        )

    assert isinstance(original, torch.Tensor)
    assert tuple(original.shape) == (1, 2048)
    expected = arr(original, np.float32)

    ref = torch.load(
        val/'ppa_model_base_reference.pt',
        map_location='cpu',
        weights_only=False
    )
    if isinstance(ref, dict):
        ref = ref['output']
    ref = arr(ref, np.float32).reshape(1, 2048)

    assert np.allclose(expected, ref, rtol=1e-3, atol=1e-3)

    status['ORIGINAL PYTORCH'] = 'PASS'
    print('ORIGINAL PYTORCH REPLAY: PASS', flush=True)

    x = arr(trace['input'], np.float32)
    fn_expected = arr(trace['fn'], np.float32)
    residual_expected = arr(trace['residual'], np.float32)

    rotary = arr(
        fn.get_rotary_embedding(x.shape[1], torch.device('cpu')),
        np.float32
    ).reshape(1, 1, 50, 256)

    deep = data['deep_in']
    wide = data['wide_in']
    tasks = data['task_in']
    sd = arr(data['sibling_deep_in'], np.int64)
    sw = arr(data['sibling_wide_in'], np.float32)

    assert len(deep) == 17
    assert len(wide) == 127
    assert len(tasks) == 2
    assert sd.shape == (1, 3, 10)
    assert sw.shape == (1, 18, 10)

    packed = [
        scalar(tasks[0]),
        scalar(tasks[1]),
        arr(data['ihq_in'], np.int64),
        arr(data['jet_name_in'], np.int64),
        arr(data['jet_status_in'], np.int64)
    ]
    packed.extend(scalar(v) for v in deep)

    packed.append(
        np.asarray(
            [arr(v).reshape(-1)[0] for v in wide],
            dtype=np.float32
        ).reshape(1, 127)
    )

    packed.extend([
        arr(data['input_ids'], np.int64),
        arr(data['attention_mask'], np.int64),
        arr(data['page_in'], np.int64),
        arr(data['item_in'], np.int64),
        arr(data['item_meta_in'], np.int64),
        arr(data['page_meta_wide_in'][0], np.float32).reshape(1, 50, 1),
        rotary
    ])

    for i in range(10):
        for j in range(3):
            packed.append(arr(sd[:, j, i], np.int64).reshape(1))
        packed.append(arr(sw[:, :, i], np.float32).reshape(1, 18))

    packed.extend([
        scalar(data['vl_in']),
        scalar(data['sibling_vl_in'])
    ])

    assert len(packed) == 72
    status['72 INPUTS'] = 'PASS'
    print('EXACT 72 INPUTS: PASS', flush=True)

    device = DeviceRef.CPU()
    graph = build_grecbase_fusion_graph_order_correct(device)
    assert len(graph.inputs) == 72

    def resolve(name):
        candidates = [name, name + '.weight']
        fn_name = re.sub(
            r'(\.ptransformer\.\d+\.)(?!fn\.)',
            r'\1fn.',
            name
        )
        if fn_name != name:
            candidates.extend([
                fn_name,
                fn_name + '.weight'
            ])
        for key in candidates:
            if key in state:
                return arr(state[key], np.float32)
        raise KeyError('Missing checkpoint weight: ' + name)

    def bind(g):
        weights = getattr(g, '_weights', None)
        if not isinstance(weights, dict):
            raise RuntimeError('Graph._weights not accessible')
        return {
            name: resolve(name)
            for name in weights.keys()
        }

    registry = bind(graph)
    assert len(registry) == 17, (
        f'Expected 17 weights, got {len(registry)}'
    )
    print('TRAINED WEIGHTS: 17/17 BOUND', flush=True)

    session = InferenceSession(devices=[CPU()])
    max_model = session.load(graph, weights_registry=registry)
    print('MAX COMPILATION: PASS', flush=True)

    actual = arr(
        max_model.execute(*packed)[0].to_numpy(),
        np.float32
    )
    assert actual.shape == (1, 2048)
    status['MAX CPU'] = 'PASS'
    print('MAX CPU EXECUTION: PASS', flush=True)

    print('\n=== EIGHT-BRANCH PARITY ===')
    flags = []

    for i, name in enumerate((
        'sequence', 'context', 'search0', 'search1',
        'jet', 'ihq', 'sibling', 'task'
    )):
        s = slice(256*i, 256*(i+1))
        diff = np.abs(actual[:, s] - expected[:, s])
        ok = bool(np.allclose(
            actual[:, s], expected[:, s],
            rtol=1e-3, atol=1e-3
        ))
        flags.append(ok)
        print(
            f'{name}: {"PASS" if ok else "FAIL"} '
            f'| max={diff.max():.8g} '
            f'| mean={diff.mean():.8g}'
        )

    status['EIGHT BRANCHES'] = (
        f'{sum(flags)}/8'
        + (' PASS' if all(flags) else ' FAIL')
    )

    diff = np.abs(actual - expected)
    full_ok = bool(np.allclose(
        actual, expected, rtol=1e-3, atol=1e-3
    ))
    status['FULL MODEL'] = 'PASS' if full_ok else 'FAIL'

    print(
        f'FULL MODEL: {status["FULL MODEL"]} '
        f'| MAX DIFF {diff.max():.8g} '
        f'| MEAN DIFF {diff.mean():.8g}'
    )

    print('\n=== DIRECT LAYER-0 PARITY ===', flush=True)

    with Graph(
        'pzaas_direct_layer0',
        input_types=[
            TensorType(DType.float32, list(x.shape), device=device),
            TensorType(DType.float32, list(rotary.shape), device=device),
            TensorType(DType.int64, [1], device=device)
        ]
    ) as lg:
        gx, gp, gv = [v.tensor for v in lg.inputs]
        block = ParallelTransformerBlockMAX(
            dtype=DType.float32,
            device=device,
            layer_idx=0
        )
        lg.output(block(gx, gp, gv))

    layer_registry = bind(lg)
    layer_model = session.load(
        lg, weights_registry=layer_registry
    )

    layer_actual = arr(
        layer_model.execute(
            x, rotary, scalar(data['vl_in'])
        )[0].to_numpy(),
        np.float32
    )

    assert layer_actual.shape == fn_expected.shape
    layer_diff = np.abs(layer_actual - fn_expected)

    layer_fn_ok = bool(np.allclose(
        layer_actual, fn_expected,
        rtol=1e-3, atol=1e-3
    ))
    residual_ok = bool(np.allclose(
        x + layer_actual, residual_expected,
        rtol=1e-3, atol=1e-3
    ))

    print(
        f'LAYER-0 FN: {"PASS" if layer_fn_ok else "FAIL"} '
        f'| MAX DIFF {layer_diff.max():.8g}'
    )
    print(
        f'LAYER-0 RESIDUAL: {"PASS" if residual_ok else "FAIL"} '
        f'| MAX DIFF '
        f'{np.abs(x + layer_actual - residual_expected).max():.8g}'
    )
    status['LAYER-0'] = (
        'PASS' if layer_fn_ok and residual_ok else 'FAIL'
    )

except Exception as exc:
    print(
        '\nVALIDATION BLOCKED:',
        type(exc).__name__, str(exc),
        flush=True
    )
    traceback.print_exc(limit=5)

finally:
    print('\n=== PROGRESS ===')
    for key, value in status.items():
        print(f'{key}: {value}')
    print('ORIGINAL DS: UNCHANGED')
    print('CTA / BPLAN: UNCHANGED')
    print('SOURCE FILES MODIFIED: NONE')

if any(v not in ('PASS', '8/8 PASS') for v in status.values()):
    raise SystemExit(1)

print('PZAAS ALL NUMERICAL PARITY: PASS')
PY
