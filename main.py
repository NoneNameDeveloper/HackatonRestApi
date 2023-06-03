import uvicorn

from src.routers import *


if __name__ == "__main__":
    uvicorn.run("src.app:app", reload=True, host="0.0.0.0", port=8095)