from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .api import api_router
from .database import engine, Base
from .config import get_settings

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app - 生产环境禁用API文档
app = FastAPI(
    title="AlgoHub API",
    description="Algorithm Capability Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - 使用明确的允许域名列表，而非通配符
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # 明确指定允许的域
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# 安全响应头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    
    # 防止MIME类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS防护 (虽然现代浏览器已弃用，但仍建议添加)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # 引用策略
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # 内容安全策略 (基础策略，可根据需要调整)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'"
    
    # 权限策略
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # 生产环境启用HSTS (仅HTTPS)
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "AlgoHub API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
