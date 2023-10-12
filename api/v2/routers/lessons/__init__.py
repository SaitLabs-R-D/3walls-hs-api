from fastapi import APIRouter, Depends
from ...middleware import login_required
from . import draft, published, archived, published_edit

router = APIRouter(dependencies=[Depends(login_required)])

router.include_router(draft.router, prefix="/draft", tags=["draft lessons"])
router.include_router(published.router, prefix="/published", tags=["published lessons"])
router.include_router(
    published_edit.router, prefix="/published/edit", tags=["edit published lessons"]
)
router.include_router(archived.router, prefix="/archived", tags=["archived lessons"])
