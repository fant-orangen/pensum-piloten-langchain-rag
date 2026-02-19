# Pensum Piloten

## Run (CLI + Gradio)

```bash
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m scripts.ingest
PYTHONPATH=. python -m scripts.gradio_app
```

Then open the local URL printed by Gradio (default: `http://127.0.0.1:7860`).
