from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from models import SiteInfo, User
from db import get_async_db
from auth_utils import get_current_user, get_current_admin
from sqlalchemy import select
from fastapi.responses import JSONResponse
from schemas import SiteInfoUpdate

router = APIRouter()


@router.get("/siteinfo")
async def get_siteinfo(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get site information. Requires authentication."""
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
    current_user: User = Depends(get_current_admin)
):
    """Update site information. Admin-only endpoint."""
    siteinfo = (await db.execute(select(SiteInfo))).scalar()
    if not siteinfo:
        # Create initial record
        siteinfo = SiteInfo(
            title=data.title or "",
            description=data.description or "",
            icp=data.icp or "",
            footer=data.footer or "",
        )
        db.add(siteinfo)
    else:
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
        "msg": "siteinfo updated successfully"
    })
