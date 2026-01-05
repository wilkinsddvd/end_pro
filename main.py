from fastapi import FastAPI, Request
from api import posts, categories, tags, archive, siteinfo, menus, auth, interaction, comments
from fastapi.responses import JSONResponse
from db import engine, Base

app = FastAPI(
    title="Blog API",
    description="RESTful API for blog system with JWT authentication",
    version="1.0.0"
)

@app.on_event("startup")
async def on_startup():
    # 自动建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 注册 API 路由
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(posts.router, prefix="/api", tags=["Posts"])
app.include_router(categories.router, prefix="/api", tags=["Categories"])
app.include_router(tags.router, prefix="/api", tags=["Tags"])
app.include_router(comments.router, prefix="/api", tags=["Comments"])
app.include_router(archive.router, prefix="/api", tags=["Archive"])
app.include_router(siteinfo.router, prefix="/api", tags=["SiteInfo"])
app.include_router(menus.router, prefix="/api", tags=["Menus"])
app.include_router(interaction.router, prefix="/api", tags=["Interaction"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 避免500返回plain text
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": {}, "msg": str(exc)}
    )

@app.get("/")
async def root():
    return JSONResponse(content={
        "code": 200,
        "data": {"message": "Welcome to Blog API"},
        "msg": "success"
    })