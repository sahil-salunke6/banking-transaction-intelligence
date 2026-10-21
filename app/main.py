
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models.transaction import Transaction
from app.api.transaction_router import router as transaction_router
from app.api.analytics_router import router as analytic_router
from app.api.risk_router import router as risk_router
from app.api.anomaly_router import router as anamoly_router
from app.api.intelligence_router import router as intelligence_router
from app.services.anomaly_service import load_model_artifact

import logging

from app.logging_config import configure_logging
from fastapi.responses import JSONResponse
from app.config import API_DOCS_ENABLED

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Load the saved ML model once during startup.
    load_model_artifact()

    yield


configure_logging()

logger = logging.getLogger(__name__)



app = FastAPI(
    title="Banking Transaction Intelligence Service",
    description="Backend service for processing and analyzing banking transactions",
    version="1.0.0",
    docs_url="/docs" if API_DOCS_ENABLED else None,
    redoc_url="/redoc" if API_DOCS_ENABLED else None,
    openapi_url="/openapi.json" if API_DOCS_ENABLED else None,
    lifespan=lifespan,
)


app.include_router(transaction_router)
app.include_router(analytic_router)
app.include_router(risk_router)
app.include_router(anamoly_router)
app.include_router(intelligence_router)



@app.exception_handler(Exception)
async def handle_unexpected_exception(request, exc):
    logger.error(
        "Unhandled application exception",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected internal server error occurred."
        },
    )


@app.get("/")
def home():
    return {
        "message": "Banking Transaction Intelligence Service is running"
    }
