from fastapi import APIRouter, Depends, Request
from ..middleware import login_required, get_user_platform
from ..middleware.platforms import PcPlatform
from services.gcp import GCP_MANAGER
from helpers.types import responses

router = APIRouter(dependencies=[Depends(login_required)])


@router.get("/lesson-viewer")
def get_lesson_viewer_software(
    _request: Request,
    platform: PcPlatform = Depends(get_user_platform),
):

    url = GCP_MANAGER.bucket_manager.generate_file_download_url(
        f"lesson-viewer/v1/1.0.0.{platform.get_extansion()}"
    )

    return responses.ApiSuccess(data={"url": url})
