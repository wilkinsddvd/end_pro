from fastapi import FastAPI, Request
from api import posts, categories, tags, archive, siteinfo, menus, auth, interaction, tickets, quick_replies, statistics, ticket_replies
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from db import engine, Base
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from api.deps import limiter
import os

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
async def on_startup():
    # 自动建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 注册 API 路由
app.include_router(posts.router, prefix="/api", tags=["Posts"])
app.include_router(categories.router, prefix="/api", tags=["Categories"])
app.include_router(tags.router, prefix="/api", tags=["Tags"])
app.include_router(archive.router, prefix="/api", tags=["Archive"])
app.include_router(siteinfo.router, prefix="/api", tags=["SiteInfo"])
app.include_router(menus.router, prefix="/api", tags=["Menus"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(interaction.router, prefix="/api", tags=["Interaction"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])
app.include_router(quick_replies.router, prefix="/api", tags=["QuickReplies"])
app.include_router(statistics.router, prefix="/api", tags=["Statistics"])
app.include_router(ticket_replies.router, prefix="/api", tags=["TicketReplies"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 避免500返回plain text
    return JSONResponse(content={"code": 500, "data": {}, "msg": str(exc)})