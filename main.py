```python
# main.py
"""
Autonomous Interview Scheduling System - Main Application Entry Point

This module serves as the entry point for the Autonomous Interview Scheduling System API.
It initializes the FastAPI application, configures middleware, authentication, and routes.
"""
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from app.api.routes import calendar_router, scheduling_router, user_router, admin_router
from app.api.auth import auth_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import verify_token
from app.db.database import init_db, close_db
from app.services.calendar_service import initialize_calendar_services
from app.services.notification_service import initialize_notification_services


# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup events
    logger.info("Starting Autonomous Interview Scheduling System...")
    
    # Initialize database connection
    await init_db()
    logger.info("Database connection established")
    
    # Initialize calendar services
    await initialize_calendar_services()
    logger.info("Calendar services initialized")
    
    # Initialize notification services
    await initialize_notification_services()
    logger.info("Notification services initialized")
    
    yield
    
    # Shutdown events
    logger.info("Shutting down Autonomous Interview Scheduling System...")
    
    # Close database connection
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for Autonomous Interview Scheduling System",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that provides basic API information.
    """
    return {
        "message": "Welcome to Autonomous Interview Scheduling System API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {"status": "healthy"}


# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(
    user_router, 
    prefix="/users", 
    tags=["Users"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    calendar_router, 
    prefix="/calendar", 
    tags=["Calendar"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    scheduling_router, 
    prefix="/scheduling", 
    tags=["Scheduling"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    admin_router, 
    prefix="/admin", 
    tags=["Admin"],
    dependencies=[Depends(verify_token)]
)


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler to catch and log unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error. Please try again later."},
    )


if __name__ == "__main__":
    """
    Run the application directly when executed as a script.
    In production, use a proper ASGI server like gunicorn with uvicorn workers.
    """
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info",
    )
```