from fastapi import APIRouter
from .routers import (
    users,
    lessons,
    accounts,
    roles,
    categories,
    watch,
    downloads,
    reviews,
    help,
)

router = APIRouter()


router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(lessons.router, prefix="/lessons")
router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(roles.router, prefix="/roles", tags=["roles"])
router.include_router(watch.router, prefix="/watch", tags=["watch lessons"])
router.include_router(downloads.router, prefix="/downloads", tags=["downloads"])
router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
router.include_router(help.router, prefix="/help", tags=["help"])
