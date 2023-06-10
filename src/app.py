from fastapi import FastAPI, Request, Response

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


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Логгирование ответов
    """
    response = await call_next(request)
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    print(f"response_body={response_body.decode()}")
    return Response(content=response_body, status_code=response.status_code,
        headers=dict(response.headers), media_type=response.media_type)