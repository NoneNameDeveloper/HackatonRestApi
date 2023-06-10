import typing

from fastapi import Depends
from pydantic import BaseModel

from starlette.responses import JSONResponse

from src.app import app

from src.models import crud, Company
from src.utils.misc import require_company


class FilterResponse(BaseModel):
    status: str
    filter_text: typing.Optional[str]


@app.get("/add_filter", tags=["Работа с фильтрами"])
async def add_filter_handler(filter: str, company: Company = Depends(require_company)) -> FilterResponse:
    """
    Добавление правила. После добавления, при обнаружении в запросе "стоп-слов", сервис будет возвращать соответствующее сообщение:
    В вопросе содержится недопустимое слово: <стоп-слово>.Пожалуйста, задайте вопрос иначе.
    """
    # добавление правила
    rule = crud.create_rule(company.company_id, filter)

    return JSONResponse(status_code=200, content={
        "status": "SUCCESS",
        "filter_text": rule.filter_text
    })


@app.get("/archive_filter", tags=["Работа с фильтрами"])
async def archive_filter_handler(rule_text: str, company: Company = Depends(require_company)) -> FilterResponse:
    """
    Архивация правила. После архивации, ограничение на слово, содержащееся в этом правиле снимаются.
    """
    # архивирование токена
    archived_text: str = crud.archive_rule(rule_text)

    if archived_text == "already":
        return JSONResponse(status_code=404, content={"status": "ALREADY_ARCHIVED"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "filter_text": archived_text})
