for p in /opt/venv/bin/python /application1/venv/bin/python /usr/local/bin/python3; do if [ -x "$p" ]; then "$p" -B -c 'import torch; print("TORCH AVAILABLE:", torch.__version__)' 2>&1; fi; done
