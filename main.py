import uvicorn

from src.routers import *


if __name__ == "__main__":
    uvicorn.run(app)