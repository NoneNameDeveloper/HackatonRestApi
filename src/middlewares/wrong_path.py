# from src.app import app
#
# from starlette.requests import Request
# from starlette.responses import JSONResponse
#
#
# # Несуществующий путь - миддлварь
# @app.middleware("http")
# async def check_path_exists(request: Request, call_next):
#     path = request.url.path
#
#     if not path.startswith("/"):
#         path = "/" + path
#
#     if path not in app.routes:
#         raise JSONResponse(status_code=404, content={"status": "BAD_REQUEST"})
#
#     return await call_next(request)
