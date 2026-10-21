from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───

    print(f"   {settings.APP_NAME} starting up...")
    print(f"   Environment: {settings.APP_ENV}")
    print(f"   Docs available at: http://localhost:8000/docs")

    yield  # ← app is live and serving requests here

    # ── SHUTDOWN ─────────────────────────────────────────
    # This runs when Ctrl+C or the container stops.
    # Close DB pools, flush caches, finish in-flight tasks.
    print(f"🛑 {settings.APP_NAME} shutting down...")


# Create the FastAPI application instance.
# This object IS your application — uvicorn runs this.
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade URL shortener with analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── MIDDLEWARE ───────
app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",  
        "http://localhost:5173",  
        "http://localhost:8080",  
    ],
    # allow_credentials=True means cookies and auth headers are included.
    # Required for JWT in Authorization header to work cross-origin.
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Authorization, Content-Type, etc.
)


# ── ROUTES ─────
# Health check
# WHY: load balancers, Docker health checks, and monitoring tools
# ping /health to know if the app is alive.
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


# Root endpoint — useful for quick sanity check
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }

