from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import SiteInfo
from db import get_async_db
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/siteinfo")
async def get_siteinfo(db: AsyncSession = Depends(get_async_db)):
    siteinfo = (await db.execute(select(SiteInfo))).scalar()
    if not siteinfo:
        return JSONResponse(content={"code": 404, "data": {}, "msg": "not initialized"})
    return JSONResponse(content={
        "code": 200,
        "data": {
            "title": siteinfo.title,
            "description": siteinfo.description,
            "icp": siteinfo.icp,
            "footer": siteinfo.footer
        },
        "msg": "success"
    })