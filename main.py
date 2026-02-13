from fastapi import FastAPI, Request
from api import posts, siteinfo, menus, auth, tickets, quick_replies
from fastapi.responses import JSONResponse
from db import engine, Base

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # 自动建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 注册 API 路由
app.include_router(posts.router, prefix="/api", tags=["Posts"])
app.include_router(siteinfo.router, prefix="/api", tags=["SiteInfo"])
app.include_router(menus.router, prefix="/api", tags=["Menus"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])
app.include_router(quick_replies.router, prefix="/api", tags=["QuickReplies"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 避免500返回plain text
    return JSONResponse(content={"code": 500, "data": {}, "msg": str(exc)})