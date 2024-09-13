# app/main.py

from fastapi import FastAPI
from routers import discovery, search
from app.database import engine, Base
from app.services.crawler import start_crawling

def create_app():
    """Initialize FastAPI app and include routers."""
    app = FastAPI(title="Centralized Intent Discovery Service")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Include routers
    app.include_router(discovery.router)
    app.include_router(search.router)

    # Start the crawler when the app starts
    @app.on_event("startup")
    async def startup_event():
        """Event handler for startup event."""
        await start_crawling()

    return app

app = create_app()