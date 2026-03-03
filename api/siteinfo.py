from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models import SiteInfo
from db import get_async_db
from sqlalchemy import select
from fastapi.responses import JSONResponse
from api.deps import get_current_user_id, require_staff
from schemas import SiteInfoUpdate

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

@router.put("/siteinfo")
async def update_siteinfo(
    data: SiteInfoUpdate,
    db: AsyncSession = Depends(get_async_db),
    user_id: int = Depends(get_current_user_id)
):
    try:
        await require_staff(user_id, db)

        siteinfo = (await db.execute(select(SiteInfo))).scalar()
        if not siteinfo:
            siteinfo = SiteInfo()
            db.add(siteinfo)

        if data.title is not None:
            siteinfo.title = data.title
        if data.description is not None:
            siteinfo.description = data.description
        if data.icp is not None:
            siteinfo.icp = data.icp
        if data.footer is not None:
            siteinfo.footer = data.footer

        await db.commit()
        await db.refresh(siteinfo)
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
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"code": e.status_code, "data": {}, "msg": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "data": {}, "msg": str(e)})