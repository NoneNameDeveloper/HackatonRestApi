import typing

from starlette.responses import JSONResponse

from src.app import app

from src.models import crud


@app.get("/add_filter", tags=["add_filter"])
async def add_filter_handler(filter: str, token: str):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # добавление правила
    rule = crud.create_rule(token, filter)

    return JSONResponse(status_code=200, content={
        "status": "SUCCESS",
        "rule_id": rule.rule_id
    })


@app.get("/archive_filter")
async def archive_filter_handler(rule_id: int, token: str):

    # проверка токена
    company = crud.get_company(token)
    if company is None:
        return JSONResponse(status_code=403, content={"status": "INVALID_API_TOKEN"})

    # архивирование токена
    crud.archive_rule(rule_id)

    return JSONResponse(status_code=200, content={"status": "SUCCESS"})
