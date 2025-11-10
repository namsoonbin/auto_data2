# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import upload, metrics, report, data, margins, auth, team
from services.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized")
    yield
    await close_db()
    print("Database connection closed")


app = FastAPI(
    title="Coupang Sales Automation API",
    description="Coupang sales and ad performance automation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
# 환경변수 FRONTEND_URL이 있으면 사용, 없으면 로컬 개발 환경
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:5173",
]

# 프로덕션 프론트엔드 URL 추가
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# CORS 설정 디버깅
print(f"CORS allowed origins: {allowed_origins}")
print(f"FRONTEND_URL env var: {frontend_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Authentication"])
app.include_router(team.router, tags=["Team Management"])
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(report.router, prefix="/api", tags=["Reports"])
app.include_router(data.router, prefix="/api", tags=["Data Management"])
app.include_router(margins.router, prefix="/api", tags=["Margin Management"])


@app.get("/")
async def root():
    return {
        "message": "Coupang Sales Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
