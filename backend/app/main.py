from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database.connection import Base, engine
from backend.app.routes import products, events, analytics, system
from backend.app.routes.insights import router as insight_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI app
app = FastAPI(
    title="Privacy-Aware User Journey Intelligence API"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# ROUTES
# =========================================================

app.include_router(
    products.router
)

app.include_router(
    events.router
)

app.include_router(
    analytics.router
)

app.include_router(
    system.router
)

app.include_router(
    insight_router
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():

    return {
        "status": "healthy"
    }