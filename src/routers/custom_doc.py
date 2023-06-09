from starlette.requests import Request
from starlette.templating import Jinja2Templates

from fastapi.staticfiles import StaticFiles


from src.app import app

app.mount(
    "/src/templates/static",
    StaticFiles(directory="src/templates/static"),
    name="static",
)

templates = Jinja2Templates(directory="src/templates")


@app.get("/docs/example", include_in_schema=False)
async def custom_doc_handler(request: Request):
    """
    Кастомная секция документации - примеры кода
    """
    return templates.TemplateResponse("code.html", context={"request": request})

