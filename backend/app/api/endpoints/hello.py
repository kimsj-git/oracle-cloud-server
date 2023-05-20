from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/hello")
async def greetings():
    content = {
        "msg": "hello!"
    }
    return JSONResponse(content=content, status_code=200)