import os

import uvicorn

from service.app import app

if __name__ == "__main__":
    if os.environ.get("ENGINE_DB_URL", None) is None:
        os.environ["ENGINE_DB_URL"] = "./service/db/service.db"

    uvicorn.run(app, host="0.0.0.0", port=8000)
