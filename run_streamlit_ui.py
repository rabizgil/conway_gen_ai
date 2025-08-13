import os

from streamlit.web import cli

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "" # Please provide your key here
    os.environ["UI_DB_URL"] = "./chatbot_interface/db/ui.db"
    cli.main_run(["./chatbot_interface/streamlit_app.py"])
