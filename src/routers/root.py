from starlette.responses import JSONResponse

from src.app import app


@app.get("/", include_in_schema=False)
async def root_path():
    return JSONResponse(status_code=404, content={"status": "BAD_REQUEST"})
