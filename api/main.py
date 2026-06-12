import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import accounts, flags, graph, websocket

logging.basicConfig(level=logging.INFO, format="%(asctime)s [api] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # anything before the yield runs on startup
    # anything after runs on shutdown
    # sqlalclchemy handles the connection pool automatically
    logging.info("api starting up...")
    yield
    logging.info("api shutting down...")
    
    
app = FastAPI(
    title="Sentinel API",
    description="real-time social media anomaly detection",
    version="1.0.0",
    lifespan=lifespan
)


# allow the frontend talk to the api, in prod; only the frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(flags.router, prefix="/flags", tags=["flags"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/health")
async def health():
    # simple health check endpoint
    return {"status": "ok"}