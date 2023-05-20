from fastapi import FastAPI
from api.api import api_router
from fastapi.responses import RedirectResponse

app = FastAPI()


@app.get("/")
def read_root():
    url = '/docs'
    response = RedirectResponse(url=url)
    return response

app.include_router(api_router, prefix="/api/v1")