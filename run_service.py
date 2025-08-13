import uvicorn
import nltk
from pathlib import Path

from service.app import app

if __name__ == "__main__":
    nltk.download("words", download_dir=Path("./nltk_data"))
    uvicorn.run(app)
