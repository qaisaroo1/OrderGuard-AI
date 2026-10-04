"""Streamlit Community Cloud entrypoint alias pointing to app.py."""
from pathlib import Path
import runpy

app_entry = Path(__file__).parent / "app.py"
runpy.run_path(str(app_entry), run_name="__main__")
