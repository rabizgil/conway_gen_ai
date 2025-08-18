import uvicorn
import nltk
from pathlib import Path

from service.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
