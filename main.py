import os
import time
import uuid
import json
import logging
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api import posts, siteinfo, menus, auth, tickets, quick_replies, stats
from db import engine, Base

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("app")

def _log(level: str, event: str, **kwargs):
    record = {"level": level, "event": event, **kwargs}
    logger.info(json.dumps(record))

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="LogisticsAPI")

# ---------------------------------------------------------------------------
# CORS – configurable via env, safe defaults for dev
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory rate limiter for auth endpoints (brute-force protection)
# ---------------------------------------------------------------------------
# Stores: { ip: [timestamp, ...] }
_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_MAX = int(os.getenv("AUTH_RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("AUTH_RATE_LIMIT_WINDOW", "60"))  # seconds

AUTH_RATE_LIMITED_PATHS = {"/api/login", "/api/register"}


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = _rate_limit_store[ip]
    # Evict old entries
    _rate_limit_store[ip] = [t for t in timestamps if t > window_start]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return True
    _rate_limit_store[ip].append(now)
    return False


# ---------------------------------------------------------------------------
# Request middleware: correlation ID, security headers, rate limiting, logging
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    # Assign or forward request/correlation ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Rate limiting for auth endpoints
    if request.url.path in AUTH_RATE_LIMITED_PATHS:
        client_ip = request.client.host if request.client else "unknown"
        if _is_rate_limited(client_ip):
            _log("warning", "rate_limit_exceeded", path=request.url.path, ip=client_ip, request_id=request_id)
            return JSONResponse(
                status_code=429,
                content={"code": 429, "data": {}, "msg": "too many requests, please try again later"},
                headers={"X-Request-ID": request_id},
            )

    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Request-ID"] = request_id

    _log(
        "info", "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )
    return response


# ---------------------------------------------------------------------------
# Database table creation on startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# Global exception handler – no stack traces to clients
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "")
    _log("error", "unhandled_exception", error=str(exc), path=str(request.url), request_id=request_id)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": {}, "msg": "internal server error"},
    )


# ---------------------------------------------------------------------------
# Register API routers
# ---------------------------------------------------------------------------
app.include_router(posts.router, prefix="/api", tags=["Posts"])
app.include_router(siteinfo.router, prefix="/api", tags=["SiteInfo"])
app.include_router(menus.router, prefix="/api", tags=["Menus"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(tickets.router, prefix="/api", tags=["Tickets"])
app.include_router(quick_replies.router, prefix="/api", tags=["QuickReplies"])
app.include_router(stats.router, prefix="/api", tags=["Stats"])
