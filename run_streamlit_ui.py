import os
from pathlib import Path

import nltk
from streamlit.web import cli

if __name__ == "__main__":
    if os.environ.get("API_URL", None) is None:
        os.environ["API_URL"] = "http://localhost:8000/cgol/game"
    if os.environ.get("UI_DB_URL", None) is None:
        os.environ["UI_DB_URL"] = "./chatbot_interface/db/ui.db"

    if os.environ.get("NLTK_DATA", None) is None:
        nltk_path = Path("./chatbot_interface/nltk_data")
        if not nltk_path.is_dir():
            try:
                nltk.find("corpora/words")
                status = True
            except LookupError as e:
                status = nltk.download("words", download_dir=nltk_path)
            if not status:
                msg = "Unable to download NLTK words corpora."
                raise LookupError(msg)

        nltk.data.path.append(str(nltk_path.absolute()))
    else:
        nltk.data.path.append(os.environ["NLTK_DATA"])

    cli.main_run(["./chatbot_interface/streamlit_app.py"])
