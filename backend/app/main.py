from __future__ import annotations
import uuid
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.routers import auth, leases, clauses, obligations, critical_dates, analytics, clause_queries

logger = logging.getLogger(__name__)

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url=None,       # disable default — we serve a branded version below
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "method=%s path=%s status=%d duration_ms=%.1f request_id=%s",
        request.method, request.url.path, response.status_code, duration_ms, request_id,
    )
    return response


PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(leases.router, prefix=PREFIX)
app.include_router(clauses.router, prefix=PREFIX)
app.include_router(obligations.router, prefix=PREFIX)
app.include_router(critical_dates.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(clause_queries.router, prefix=PREFIX)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.exception("Unhandled exception request_id=%s: %s", request_id, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return JSONResponse(status_code=405, content={"detail": "Method not allowed"})


@app.get("/health")
async def health():
    """Liveness check — fast, no dependencies."""
    return {"status": "ok", "app": settings.APP_NAME, "version": app.version}


@app.get("/ready")
async def ready():
    """Readiness check — pings the database. AI key presence is reported but
    does not block readiness (OpenAI is optional thanks to rule-based fallbacks).
    """
    from sqlalchemy import text
    from app.database import AsyncSessionLocal

    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("readiness.db_failed: %s", e)

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "checks": {
            "database": "ok" if db_ok else "fail",
            "ai_configured": bool(settings.OPENAI_API_KEY),
        },
    }


# ── Branded Swagger UI ─────────────────────────────────────────────────────────
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} — API Docs",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
    )
    # Inject branded CSS into the returned HTML
    branded_css = """
    <style>
      /* ── LeaseIQ AI — Branded Swagger UI ── */
      body { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; background: #f9fafb; }

      /* Brand top bar */
      .swagger-ui .topbar { background: #1e1b4b; padding: 14px 24px; }
      .swagger-ui .topbar .download-url-wrapper { display: none !important; }
      .swagger-ui .topbar-wrapper .link::after {
        content: 'LeaseIQ AI — API Reference';
        color: #e0e7ff;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: -0.3px;
      }
      .swagger-ui .topbar-wrapper .link img { display: none; }

      /* Brand accent bar at very top */
      body::before {
        content: '';
        display: block;
        height: 4px;
        background: linear-gradient(90deg, #4f46e5, #6366f1, #818cf8);
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9999;
      }

      /* Info section */
      .swagger-ui .info .title { color: #1e1b4b !important; }
      .swagger-ui .info .base-url { color: #6366f1; }

      /* HTTP method chips — brand indigo for POST */
      .swagger-ui .opblock.opblock-post .opblock-summary-method { background: #4f46e5 !important; }
      .swagger-ui .opblock.opblock-get  .opblock-summary-method { background: #0ea5e9 !important; }
      .swagger-ui .opblock.opblock-patch .opblock-summary-method { background: #f59e0b !important; }
      .swagger-ui .opblock.opblock-delete .opblock-summary-method { background: #ef4444 !important; }

      /* Execute button */
      .swagger-ui .btn.execute { background: #4f46e5 !important; border-color: #4f46e5 !important; }
      .swagger-ui .btn.execute:hover { background: #4338ca !important; }

      /* Schema models */
      .swagger-ui section.models { background: #f9fafb; border-color: #e5e7eb; }
      .swagger-ui section.models .model-box { background: #ffffff; }
    </style>
    """
    # Insert branded CSS just before </head>
    body = html.body.decode("utf-8")
    body = body.replace("</head>", branded_css + "\n</head>", 1)
    return HTMLResponse(content=body, status_code=200)
