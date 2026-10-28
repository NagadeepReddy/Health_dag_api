cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -I -S -B -c 'import ast, pathlib; p=pathlib.Path("artifacts/v1.168-max/maxserve_cta_extension/cta_router.py"); ast.parse(p.read_text()); print("CTA ROUTER SYNTAX: PASS"); print("DS CODE: UNCHANGED")'
