cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import re
import textwrap

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
source = p.read_text()
marker = "CTA_ONLY_FACTORY_BRIDGE"

if marker in source:
    print("CTA FACTORY BRIDGE: ALREADY INSTALLED")
else:
    match = re.search(
        r"^([ \t]*)register_cta_architecture\(\)[ \t]*$",
        source,
        re.MULTILINE
    )
    assert match, "Registration anchor missing; no changes made"

    indent = match.group(1)

    patch = textwrap.dedent("""
        # CTA_ONLY_FACTORY_BRIDGE
        from max.pipelines.lib import PIPELINE_REGISTRY
        from maxserve_cta_extension.cta_spawn_worker import CTAFactoryWrapper

        original_retrieve_factory = PIPELINE_REGISTRY.retrieve_factory

        def cta_retrieve_factory(config, *args, **kwargs):
            model_config = getattr(config, "model_config", None)
            model_path = getattr(model_config, "model_path", None)

            if model_path is not None and str(model_path).rstrip("/").endswith("/cta_native_model"):
                print("CTA: native factory selected without text tokenizer", flush=True)
                return None, CTAFactoryWrapper(None)

            return original_retrieve_factory(config, *args, **kwargs)

        PIPELINE_REGISTRY.retrieve_factory = cta_retrieve_factory
    """).strip("\n")

    patch = textwrap.indent(patch, indent)

    position = source.find("\n", match.end())
    assert position >= 0, "Unexpected file ending"

    updated = source[:position+1] + patch + "\n" + source[position+1:]
    compile(updated, str(p), "exec")

    backup = p.with_name(p.name + ".before_cta_factory_bridge")
    assert not backup.exists(), "Backup exists; no changes made"

    backup.write_text(source)
    p.write_text(updated)

    print("CTA FACTORY BRIDGE: INSTALLED")
    print("MAX-ONLY SYNTAX: PASS")
    print("BACKUP: SAVED")

print("ORIGINAL DS FILES: UNCHANGED")
PY
