from fastapi import APIRouter, Depends, Query
from ...middleware import login_required, check_user_permission, Resources, Actions
from services.gcp import GCP_MANAGER, FoldersNames as GCPFoldersNames
from helpers.files import (
    get_video_mime_type,
    get_image_mime_type,
    get_file_extension_from_mime_type,
)
from helpers.validators import valid_url
from helpers.types import responses, RequestWithUserId, RequestWithDraft
import time
from db import updates, queries, transactions
from . import models
from google.cloud.exceptions import NotFound

router = APIRouter(
    dependencies=[Depends(login_required)],
)


def require_draft_lesson(request: RequestWithUserId):
    draft = queries.get_draft_lesson_by_creator(request.state.user_id)

    if not draft.success:
        return responses.ApiRaiseError(message="draft not found")

    request.state.draft = draft.value


@router.get(
    "",
    dependencies=[
        Depends(
            check_user_permission(
                {Resources.DRAFT_LESSONS: [Actions.CREATE, Actions.READ]}
            )
        )
    ],
)
def get_draft_lesson(request: RequestWithUserId):
    draft_res = updates.get_or_create_draft_lesson(request.state.user_id)

    if draft_res.failure:
        return responses.ApiError()

    draft = draft_res.value
    
    for part in draft.parts:
        if part.gcp_path:
            part.gcp_path = GCP_MANAGER.bucket_manager.generate_file_download_url(
                part.gcp_path
            )
    
    draft_data = draft_res.value.dict()

    return responses.ApiSuccess(data=draft_data)


@router.put(
    "",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
        Depends(require_draft_lesson),
    ],
)
def edit_draft_lesson_basic_info(
    request: RequestWithDraft, data: models.EditDraftLessonBasicInfoPayload
):
    draft = request.state.draft

    thumbnail = None
    description_file = None

    if isinstance(data.categories, list):
        if data.categories:
            if not len(data.categories) == len(set(data.categories)):
                return responses.ApiError(message="duplicate categories")
            category_res = queries.validate_many_categories_exists(data.categories)

            if not category_res.success:
                return responses.ApiError(
                    message="error validating categories", code=500
                )

            if not category_res.value:
                return responses.ApiError(message="invalid categories")

    if data.thumbnail:
        file_type = get_file_extension_from_mime_type(data.thumbnail[1])

        if file_type is None:
            return responses.ApiError(message="invalid file type")

        # upload the image to the bucket and get the url (publicly accessible)
        url = GCP_MANAGER.upload_lesson_thumbnail(
            data.thumbnail[0], str(draft.id), file_type, data.thumbnail[1]
        )

        thumbnail = url

    if data.description_file:
        file_name = GCP_MANAGER.upload_lesson_description_file(
            data.description_file[0], str(draft.id)
        )

        description_file = file_name

    draft_update_res = updates.update_draft_lesson_by_id(
        draft.id,
        title=data.title,
        description=data.description,
        description_file=description_file,
        categories=data.categories,
        thumbnail=thumbnail,
        credit=data.credit,
    )

    if draft_update_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess()


@router.delete(
    "",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.DELETE]})),
        Depends(require_draft_lesson),
    ],
)
def delete_draft_lesson(request: RequestWithDraft):
    draft = request.state.draft

    try:
        GCP_MANAGER.delete_lesson(str(draft.id))
    # gcp throws an error if the file doesn't exist and we don't care about it
    except NotFound:
        pass
    except Exception as e:
        return responses.ApiError(message="error deleting files from gcp")

    updates.delete_draft_lesson_by_id(draft.id)

    return responses.ApiSuccess()


@router.post(
    "/part",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
        Depends(require_draft_lesson),
    ],
)
def add_part_to_draft_lesson(request: RequestWithDraft, data: models.AddPartPayload):
    draft = request.state.draft

    if not len(set(data.old_parts_order.keys())) == len(draft.parts):
        return responses.ApiError(
            code=400,
            message="old parts order length is not equal to draft parts length",
        )
    elif not len(set(data.old_parts_order.values())) == len(
        set(data.old_parts_order.values())
    ):
        return responses.ApiError(
            code=400,
            message="old parts order values are not unique",
        )

    for part in draft.parts:
        new_order = data.old_parts_order.get(part.id)

        if new_order is None:
            return responses.ApiError(
                code=400,
                detail={"message": f"part {part.id} not found in old parts order"},
            )

        if new_order < 0:
            return responses.ApiError(
                code=400,
                detail={"message": f"part {part.id} new order is negative"},
            )

        part.order = new_order

    update_part_res = updates.add_part_to_draft_lesson(
        draft, data.new_part_order, data.part_type
    )

    if update_part_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess(
        data={
            "part_id": update_part_res.value.parts[-1].id,
            "part_index": data.new_part_order,
        },
        message="part added successfully",
    )


@router.post(
    "/parts/order",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
    ],
)
def edit_parts_order_in_draft_lesson(request: RequestWithUserId, data: dict[str, int]):
    update_res = updates.reorder_parts_in_draft_lesson(request.state.user_id, data)

    if update_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess(message="parts order updated successfully")


@router.delete(
    "/part",
    dependencies=[
        Depends(
            check_user_permission(
                {Resources.DRAFT_LESSONS: [Actions.UPDATE, Actions.DELETE]}
            )
        ),
    ],
)
def delete_part_from_draft_lesson(
    request: RequestWithUserId, part_id: str = Query(...)
):
    # TODO change to transaction
    update_res = updates.remove_part_from_draft_lesson(request.state.user_id, part_id)

    if update_res.failure:
        return responses.ApiError()

    draft = update_res.value

    GCP_MANAGER.delete_lesson_part(str(draft.id), part_id)

    return responses.ApiSuccess(message="part deleted successfully")


@router.get(
    "/part/upload-link",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
        Depends(require_draft_lesson),
    ],
)
def get_file_upload_link(
    request: RequestWithDraft,
    screen_side: int = Query(..., gt=-1, lt=3),
    part_id: str = Query(...),
    file_type: str = Query(...),
    is_video: bool = Query(default=False),
    is_image: bool = Query(default=False),
):
    draft = request.state.draft

    if not is_video and not is_image:
        return responses.ApiError(
            message="is_video and is_image can't both be false",
        )

    mime_type = None

    if is_video:
        mime_type = get_video_mime_type(file_type)
    elif is_image:
        mime_type = get_image_mime_type(file_type)

    if mime_type is None:
        return responses.ApiError(message="invalid file type")

    lesson_id = str(draft.id)

    part = draft.get_part(part_id)

    if not part:
        return responses.ApiError(message="part not found")

    if not part.is_normal():
        return responses.ApiError(message="Cant upload file to the given part type")

    upload_path = f"{GCPFoldersNames.LESSONS}/{lesson_id}/{part_id}/{screen_side}-{time.time()}.{file_type}"

    upload_link = GCP_MANAGER.bucket_manager.generate_file_upload_url(
        upload_path, mime_type
    )

    return responses.ApiSuccess(
        data={
            "upload_link": upload_link,
            "upload_path": upload_path,
        }
    )


@router.put(
    "/part/screen",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
        Depends(require_draft_lesson),
    ],
)
def update_part_screen_in_draft_lesson(
    request: RequestWithDraft, data: models.UpdatePartDataPayload
):
    # TODO change to transaction
    draft = request.state.draft

    part = draft.get_part(data.part_id)

    if part is None:
        return responses.ApiError(message="part not found")

    if not part.is_normal():
        return responses.ApiError(message="Cant update screen of the given part type")

    mime_type = None

    # if the given screen is a media screen will check if the file exists in the bucket
    if data.media:
        # check if the given url is for the givem draft lesson
        if str(draft.id) not in data.url:
            return responses.ApiError(message="invalid media url")
        # try to get the file from the bucket and its metadata
        try:
            file = GCP_MANAGER.bucket_manager.get_file_blob(data.url)
            file.patch()
        except:
            return responses.ApiError(message="invalid media url")
        # set the mime type
        mime_type = file.content_type
    else:
        if not valid_url(data.url):
            return responses.ApiError(message="invalid url")

    screen = part.screens[data.screen]

    # clear the old screen saved files by filtering the files that are not the new url, and delete them
    GCP_MANAGER.delete_part_screen_old_media(
        str(draft.id), data.part_id, screen, data.url
    )

    screen.mime_type = mime_type
    screen.url = data.url
    screen.type_ = data.type_.value
    screen.comment = data.comment

    updates.update_part_screen_in_draft_lesson(
        draft.id,
        data.part_id,
        data.screen,
        screen,
    )

    return responses.ApiSuccess(message="part screen updated successfully")


@router.put(
    "/part/title",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
    ],
)
def update_part_title_in_draft_lesson(
    request: RequestWithUserId, title: str = Query(...), part_id: str = Query(...)
):
    update_res = updates.update_part_title_in_draft_lesson(
        request.state.user_id, part_id, title
    )

    if update_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess(message="part title updated successfully")


@router.post(
    "/publish",
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.DRAFT_LESSONS: [Actions.DELETE],
                    Resources.PUBLISHED_LESSONS: [Actions.CREATE],
                }
            )
        ),
        Depends(require_draft_lesson),
    ],
)
def publish_draft_lesson(request: RequestWithDraft):
    draft = request.state.draft

    publish_res = transactions.publish_draft_lesson(draft, request)

    if not publish_res.success:
        return responses.ApiError(message="lesson publish failed")

    return responses.ApiSuccess(message="lesson published successfully")


@router.get(
    "/description-file",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.READ]})),
        Depends(require_draft_lesson),
    ],
)
def get_draft_lesson_description_file(request: RequestWithDraft):
    draft = request.state.draft

    if not draft.description_file:
        return responses.ApiError(message="description file not found")

    url = GCP_MANAGER.bucket_manager.generate_file_download_url(draft.description_file)

    return responses.ApiSuccess(data={"url": url})


@router.put(
    "/part/panaromic",
    dependencies=[
        Depends(check_user_permission({Resources.DRAFT_LESSONS: [Actions.UPDATE]})),
        Depends(require_draft_lesson),
    ],
)
def update_part_panoramic(
    request: RequestWithDraft, payload: models.UpdatePartPanoramicPayload = Depends()
):
    if not payload.image and not payload.panoramic_url:
        return responses.ApiError(message="no image or url provided")
    elif payload.image and payload.panoramic_url:
        return responses.ApiError(message="can't provide both image and url")
    
    if payload.image and not payload.image.content_type.startswith("image/"):
        return responses.ApiError(message="invalid image type")

    draft = request.state.draft

    part = draft.get_part(payload.part_id)

    if part is None:
        return responses.ApiError(message="part not found")

    if not part.is_panoramic():
        return responses.ApiError(
            message="Cant update panoramic of the given part type"
        )
    
    new_panormic_path = None

    if payload.panoramic_url:
        
        res = updates.update_draft_part_panoramic(draft.id, payload.part_id, "", payload.panoramic_url)
    else:
        try:
            new_panormic_path = GCP_MANAGER.upload_lesson_part_panoramic(
                str(draft.id),
                payload.part_id,
                payload.image.file,
                payload.image.filename,
                payload.image.content_type,
            )
        except:
            return responses.ApiError(message="error uploading panoramic image")

        res = updates.update_draft_part_panoramic(draft.id, payload.part_id, new_panormic_path, "")
    
    if res.failure:
        return responses.ApiError(message="error updating panoramic image")
    
    try:
        GCP_MANAGER.delete_lesson_part_old_panoramic(
            str(draft.id), payload.part_id, exclude=new_panormic_path
        )
    # Thats ok
    except:
        pass
    
    if new_panormic_path:
        panormic_url = GCP_MANAGER.bucket_manager.generate_file_download_url(
            new_panormic_path
        )
    else:
        panormic_url = payload.panoramic_url

    return responses.ApiSuccess(
        message="panoramic updated successfully", data={"url": panormic_url}
    )
