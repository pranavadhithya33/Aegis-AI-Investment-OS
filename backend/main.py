import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.notifications import notification_broker
from backend.scheduler import scheduler_daemon
from backend.routers.assets import router as assets_router
from backend.routers.portfolio import router as portfolio_router
from backend.routers.simulation import router as simulation_router
from backend.routers.ai import router as ai_router

# Setup logging
logging.basicConfig(
    level=logging.getLevelName(settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing Aegis AI backend services...")
    notification_broker.start()
    scheduler_daemon.start()
    
    yield
    
    # Shutdown actions
    logger.info("Stopping Aegis AI backend services...")
    scheduler_daemon.stop()

app = FastAPI(
    title="Aegis AI - API Engine",
    description="Deterministic portfolio management, quantitative simulations, and LLM consensus decision pipeline.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Next.js / PWA frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(assets_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

@app.get("/")
def health_check():
    """Simple status check API."""
    return {
        "status": "healthy",
        "app": "Aegis AI API Engine",
        "version": "1.0.0",
        "env": settings.ENV
    }
