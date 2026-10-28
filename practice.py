cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -I -S -B -c 'import ast,pathlib; d=pathlib.Path("artifacts/v1.168-max/maxserve_cta_extension"); files=sorted(d.glob("*.py")); [ast.parse(p.read_text(),filename=str(p)) for p in files]; print("MAX EXTENSION SYNTAX: PASS"); print("FILES CHECKED:",len(files)); print("NO MAX STARTUP OR DS EXECUTION")'
