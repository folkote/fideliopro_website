"""
Run script for FidelioPro FastAPI application.
"""

import asyncio
import socket
import sys

import uvicorn
from app.config import settings

# psycopg3 requires SelectorEventLoop; on Windows the default is ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Connect to a remote address to determine the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    # Configure uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"],
        },
    }

    print(f"Starting {settings.app_name} v{settings.app_version}")
    print()
    
    # Show multiple access URLs when host is 0.0.0.0
    if settings.host == "0.0.0.0":
        local_ip = get_local_ip()
        print("Server will be available at:")
        print(f"  Local:    http://localhost:{settings.port}")
        print(f"  Network:  http://{local_ip}:{settings.port}")
        print()
        print("API documentation:")
        print(f"  Local:    http://localhost:{settings.port}/docs")
        print(f"  Network:  http://{local_ip}:{settings.port}/docs")
        print()
        print("Health check:")
        print(f"  Local:    http://localhost:{settings.port}/health")
        print(f"  Network:  http://{local_ip}:{settings.port}/health")
    else:
        print(f"Server will be available at: http://{settings.host}:{settings.port}")
        print(f"API documentation: http://{settings.host}:{settings.port}/docs")
        print(f"Health check: http://{settings.host}:{settings.port}/health")
    
    print()

    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_config=log_config,
        reload=settings.debug,
        access_log=False,  # We handle access logging in middleware
    )
