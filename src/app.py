from fastapi import FastAPI

from src.middlewares import *
from src.routers import *


app = FastAPI()

app = FastAPI(
    title="Умный Ассистент",
    description="""
Умный корпоративный ассистент для помощи в решении бизнес-задач.\n\n<a href='/docs/example/'>Check Example</a>
""",
    version="0.0.2"
)
