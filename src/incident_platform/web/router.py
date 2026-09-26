from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


WEB_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = WEB_DIRECTORY / "static"
INDEX_FILE = WEB_DIRECTORY / "index.html"


router = APIRouter(
    tags=["Dashboard"],
)


router.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static",
)


@router.get(
    "/dashboard",
    response_class=FileResponse,
)
def dashboard() -> FileResponse:
    """Serve the operational dashboard."""

    return FileResponse(INDEX_FILE)
