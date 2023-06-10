from src.models.company import Company


class AccessException(Exception):
    pass


def require_company(token: str):
    """
    зависимость для роутеров, которая получает данные о компании по ID
    """
    company = Company.get_by_token(token)
    if not company:
        raise AccessException()
    return company

