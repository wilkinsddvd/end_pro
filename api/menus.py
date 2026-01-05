from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import Menu
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/menus")
async def get_menus(db: AsyncSession = Depends(get_async_db)):
    try:
        result = await db.execute(select(Menu))
        menus = result.scalars().all()
        out = []
        for m in menus:
            item = {"title": m.title}
            if m.path:
                item["path"] = m.path
            if m.url:
                item["url"] = m.url
            out.append(item)
        return JSONResponse(content={"code": 200, "data": {"menus": out}, "msg": "success"})
    except Exception as e:
        return JSONResponse(content={"code": 500, "data": {}, "msg": str(e)})