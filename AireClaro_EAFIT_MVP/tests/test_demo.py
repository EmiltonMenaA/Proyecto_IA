"""Offline smoke tests for the runnable Streamlit demo (no API key/network)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP_DIR = Path(__file__).resolve().parents[1] / ".test-tmp"
TEMP_DIR.mkdir(exist_ok=True)
tempfile.tempdir = str(TEMP_DIR)
os.environ.update({"TMP": str(TEMP_DIR), "TEMP": str(TEMP_DIR), "TMPDIR": str(TEMP_DIR)})

from streamlit.testing.v1 import AppTest


class AireClaroDemoTests(unittest.TestCase):
    def launch(self):
        # Force deterministic local mode even if a key exists in the host environment.
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "AIRECLARO_SOURCE": "demo", "TMP": str(TEMP_DIR), "TEMP": str(TEMP_DIR), "TMPDIR": str(TEMP_DIR)}):
            return AppTest.from_file("app.py").run(timeout=40)

    def test_dashboard_loads_without_errors(self):
        app = self.launch()
        self.assertEqual([], list(app.exception))
        self.assertEqual(1, len(app.chat_input))
        self.assertEqual(3, len(app.button))
        self.assertIn("210", [metric.value for metric in app.metric])

    def test_prediction_button_shows_model_and_baseline(self):
        app = self.launch()
        next(button for button in app.button if "predicción" in button.label.lower()).click().run(timeout=40)
        self.assertEqual([], list(app.exception))
        response = app.chat_message[-1].markdown[0].value
        self.assertIn("Naive Bayes", response)
        self.assertIn("línea base", response)

    def test_sources_button_runs_local_retrieval(self):
        app = self.launch()
        next(button for button in app.button if "fuentes" in button.label.lower()).click().run(timeout=40)
        self.assertEqual([], list(app.exception))
        self.assertEqual("Herramientas usadas: search_docs", app.chat_message[-1].caption[0].value)


if __name__ == "__main__":
    unittest.main()
