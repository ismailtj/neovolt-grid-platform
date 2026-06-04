import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from db import SessionLocal, engine
from routers import auth, clients, compteurs, meteo, releves, stats
from auth import ensure_default_user

logger = logging.getLogger("uvicorn.error")

env = os.getenv("APP_ENV", "development").lower()
docs_url = "/docs" if env != "production" else None
redoc_url = "/redoc" if env != "production" else None
openapi_url = "/openapi.json" if env != "production" else None

app = FastAPI(
    title="Néovolt Energy Platform API",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# CORS policy - permissive for development/tests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(compteurs.router)
app.include_router(meteo.router)
app.include_router(releves.router)
app.include_router(stats.router)


@app.get("/")
def read_root():
    return {"status": "online", "project": "Néovolt"}


@app.get("/health/db")
def health_db():
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return {"database": "connected"}
    except SQLAlchemyError as exc:
        logger.exception("DB health check failed")
        raise HTTPException(status_code=500, detail="Database error occurred. Please try again later.")
    finally:
        session.close()


@app.on_event("startup")
def on_startup():
    ensure_default_user()
    logger.info("API startup: configuration loaded and application initialized.")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("API shutdown: disposing DB engine.")
    try:
        engine.dispose()
        logger.info("DB engine disposed successfully.")
    except Exception:
        logger.exception("Error while disposing DB engine")


@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred. Please try again later."},
    )
