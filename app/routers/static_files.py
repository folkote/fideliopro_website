"""
Static files router for serving website and SQL files.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..utils.logger import logger


# Create static files router
router = APIRouter()

# Initialize templates (if using template rendering)
templates = Jinja2Templates(directory=settings.website_dir)


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Main website page",
    description="Serve the main website page",
)
async def serve_index(request: Request):
    """
    Serve the main website index page.
    """
    try:
        index_path = Path(settings.website_dir) / "index.html"

        if not index_path.exists():
            logger.error("Index file not found", path=str(index_path))
            raise HTTPException(status_code=404, detail="Website not found")

        # Read and return the HTML file
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Main page logging is handled by middleware
        return HTMLResponse(content=content)

    except FileNotFoundError:
        logger.error("Index file not found")
        raise HTTPException(status_code=404, detail="Website not found")
    except Exception as e:
        logger.error("Error serving index page", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/favicon.ico",
    response_class=FileResponse,
    summary="Serve favicon",
    description="Serve the website favicon",
)
async def serve_favicon():
    """
    Serve the website favicon.
    """
    try:
        favicon_path = Path(settings.website_dir) / "favicon.ico"

        if not favicon_path.exists():
            # Try alternative locations
            alt_paths = [
                Path(settings.static_dir) / "favicon.ico",
                Path(settings.website_dir) / "images" / "favicon.ico",
                Path(settings.website_dir) / "img" / "favicon.ico",
            ]

            for alt_path in alt_paths:
                if alt_path.exists():
                    favicon_path = alt_path
                    break
            else:
                logger.warning("Favicon not found")
                raise HTTPException(status_code=404, detail="Favicon not found")

        return FileResponse(
            path=str(favicon_path), media_type="image/x-icon", filename="favicon.ico"
        )

    except Exception as e:
        logger.error("Error serving favicon", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{filename:path}",
    summary="Serve static files",
    description="Serve SQL files and other static content",
)
async def serve_static_file(filename: str, request: Request):
    """
    Serve static files (SQL files, images, CSS, JS, etc.).

    This endpoint maintains compatibility with the original Flask application
    for serving SQL files and other static content.
    """
    try:
        # Security: prevent directory traversal
        if ".." in filename or filename.startswith("/"):
            logger.warning(
                "Directory traversal attempt",
                filename=filename,
                ip=request.client.host if request.client else "unknown",
            )
            raise HTTPException(status_code=403, detail="Access denied")

        # Determine file type and location
        file_path = None
        media_type = None

        if filename.endswith(".sql"):
            # SQL files
            file_path = Path(settings.sql_dir) / filename
            media_type = "text/plain"

        elif filename.endswith(
            (
                ".css",
                ".js",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".ico",
                ".svg",
                ".woff",
                ".woff2",
                ".ttf",
                ".eot",
            )
        ):
            # Website assets
            file_path = Path(settings.website_dir) / filename

            # Determine media type
            if filename.endswith(".css"):
                media_type = "text/css"
            elif filename.endswith(".js"):
                media_type = "application/javascript"
            elif filename.endswith(".png"):
                media_type = "image/png"
            elif filename.endswith((".jpg", ".jpeg")):
                media_type = "image/jpeg"
            elif filename.endswith(".gif"):
                media_type = "image/gif"
            elif filename.endswith(".svg"):
                media_type = "image/svg+xml"
            elif filename.endswith((".woff", ".woff2")):
                media_type = "font/woff"
            elif filename.endswith(".ttf"):
                media_type = "font/ttf"
            elif filename.endswith(".eot"):
                media_type = "application/vnd.ms-fontobject"
            else:
                media_type = "application/octet-stream"

        elif filename.endswith(".html"):
            # HTML files
            file_path = Path(settings.website_dir) / filename
            media_type = "text/html"

        else:
            # Try to find file in website directory
            file_path = Path(settings.website_dir) / filename
            media_type = "application/octet-stream"

        # Check if file exists
        if not file_path or not file_path.exists():
            logger.warning(
                "File not found",
                filename=filename,
                path=str(file_path) if file_path else "None",
            )
            raise HTTPException(status_code=404, detail="File not found")

        # Check if it's actually a file (not a directory)
        if not file_path.is_file():
            logger.warning("Path is not a file", filename=filename, path=str(file_path))
            raise HTTPException(status_code=404, detail="File not found")

        # Static file logging is handled by middleware

        return FileResponse(
            path=str(file_path), media_type=media_type, filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error serving static file", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
