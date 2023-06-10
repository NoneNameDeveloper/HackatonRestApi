import typing

from starlette.responses import JSONResponse

from src.models import crud

from src.app import app


@app.get("/create_company", tags=["Работа с черным списком ресурсов"])
async def create_company_handler(company_id: int, company_name: typing.Optional[str]):
    """
    Создание компании (ID Telegram чата, в который добавили демонстрационного бота)
    """
    company = crud.create_company(company_id=company_id, company_name=company_name)
    return JSONResponse(status_code=200, content={"status": "SUCCESS", "company_token": company[1]})


@app.get("/get_company", tags=["Работа с черным списком ресурсов"])
async def get_company_handler(company_id: int):
    """
    Получение информации по компании по ID
    """
    company = crud.get_company_by_id(company_id)

    if company is None:
        return JSONResponse(status_code=404, content={"status": "NOT_FOUND"})

    return JSONResponse(status_code=200, content={"status": "SUCCESS", "company_id": company.company_id, "company_name": company.company_name})
