import typing

from fastapi import Depends
from pydantic import BaseModel

from starlette.responses import JSONResponse

from src.app import app

from src.models import crud, Company
from src.utils.misc import require_company


class FilterCreateResponse(BaseModel):
    status: str
    rule_id: typing.Optional[int]


class FilterArchiveResponse(BaseModel):
    status: str
    archived_text: typing.Optional[str]


@app.get("/add_filter", tags=["Работа с фильтрами"])
async def add_filter_handler(filter: str, company: Company = Depends(require_company)) -> FilterCreateResponse:
    """
    Добавление правила. После добавления, при обнаружении в запросе "стоп-слов", сервис будет возвращать соответствующее сообщение:
    В вопросе содержится недопустимое слово: <стоп-слово>.Пожалуйста, задайте вопрос иначе.
    """
    # добавление правила
    rule = crud.create_rule(company.company_id, filter)

    return JSONResponse(status_code=200, content={
        "status": "SUCCESS",
        "rule_id": rule.rule_id
    })


@app.get("/archive_filter", tags=["Работа с фильтрами"])
async def archive_filter_handler(rule_id: int, company: Company = Depends(require_company)) -> FilterArchiveResponse:
    """
    Архивация правила. После архивации, ограничение на слово, содержащееся в этом правиле снимаются.
    """
    # архивирование токена
    archived_text: str = crud.archive_rule(rule_id)

    if archived_text == "already":
        return JSONResponse(status_code=404, content={"status": "ALREADY_ARCHIVED"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "archived_text": archived_text})
