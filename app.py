"""
Entrypoint para Hugging Face Spaces (Streamlit).
Al ejecutar 'streamlit run app.py', se carga la app definida en app/main.py.
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import app.main  # noqa: E402
