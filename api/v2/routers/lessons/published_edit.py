from fastapi import APIRouter, Depends, Path, Query
from ...middleware import check_user_permission, Actions, Resources
from helpers.types import (
    RequestWithFullUser,
    responses,
    PublishedLessonPopulateOptions,
    UserPopulateOptions,
)
from helpers.validators import valid_url
from helpers import fields
from helpers.files import (
    get_file_extension_from_mime_type,
    get_image_mime_type,
    get_video_mime_type,
)
import time
from db import queries, updates, transactions
from db.models import ScreensTypes, LessonPart, LessonScreen
from . import models
from services.gcp import GCP_MANAGER, FoldersNames as GCPFoldersNames
from google.cloud.exceptions import NotFound

router = APIRouter(
    dependencies=[
        Depends(
            check_user_permission(
                {
                    Resources.PUBLISHED_LESSONS: [
                        Actions.UPDATE,
                    ]
                }
            )
        )
    ]
)


@router.put(
    "/{lesson_id}",
)
def start_editing_published_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        # will populate the current editor and the initial editor
        # with their roles
        populate=PublishedLessonPopulateOptions(
            current_editor=UserPopulateOptions(role=True),
            initial_editor=UserPopulateOptions(role=True),
        ),
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    start_edit_res = None

    if lesson.mid_edit:
        if lesson.edit_data.current_editor.id == request.state.user.id:
            return responses.ApiError(
                code=200,
                message="you are already editing this lesson",
            )
        elif lesson.edit_data.initial_editor.id == request.state.user.id:
            return responses.ApiError(
                code=200,
                message="you are the initial editor of this lesson but someone else is editing it",
            )
        else:
            # if the user has higher role than the initial editor he can edit the lesson
            # higher role is lower number
            if (
                lesson.edit_data.initial_editor.role.rank > request.state.user.role.rank
                or request.state.user.role.rank == 0
            ):
                start_edit_res = updates.change_current_editor_of_published_lesson(
                    lesson_id, request.state.user.id, lesson.edit_data.current_editor.id
                )
    else:
        start_edit_res = updates.start_editing_published_lesson(
            lesson, request.state.user.id
        )

    if start_edit_res is None:
        return responses.ApiError(
            code=403,
            message="you are not allowed to edit this lesson",
        )

    if start_edit_res.failure:
        if start_edit_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        code=200,
        message="lesson editing started",
    )


@router.get(
    "/{lesson_id}",
)
def get_edit_data_of_published_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):
    lesson_res = queries.get_published_mid_edit_lesson_for_external(
        lesson_id,
        request,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    edit_data = {
        key: value
        for key, value in lesson.pop("edit_data").items()
        if not value == None
    }

    parts = edit_data.pop("parts", [])
    
    for part in parts:
        if part.get("gcp_path"):
            part["gcp_path"] = GCP_MANAGER.bucket_manager.generate_file_download_url(
                part["gcp_path"]
            )
    
    return responses.ApiSuccess(
        data={
            **lesson,
            **edit_data,
            "parts": parts
        }
    )


@router.post("/{lesson_id}")
def edit_published_lesson_basic_info_by_id(
    request: RequestWithFullUser,
    data: models.EditPublishedLessonBasicInfoPayload,
    lesson_id: fields.ObjectIdField = Path(...),
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    thumbnail = None

    description_file = None

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

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
            data.thumbnail[0], str(lesson_id), file_type, data.thumbnail[1], edit=True
        )

        thumbnail = url

    if data.description_file:
        file_name = GCP_MANAGER.upload_lesson_description_file(
            data.description_file[0], str(lesson_id), edit=True
        )

        description_file = file_name

    update_res = updates.update_published_lesson_base_edit_data(
        lesson_id,
        request=request,
        title=data.title,
        categories=data.categories,
        thumbnail=thumbnail,
        description=data.description,
        description_file=description_file,
        credit=data.credit,
    )

    if update_res.failure:
        if update_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        code=200,
        message="edited",
    )


@router.delete(
    "/{lesson_id}",
)
def delete_edit_data_of_published_lesson_by_id(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):
    tran_res = transactions.delete_edit_data(
        lesson_id,
        request,
    )

    if not tran_res.success:
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        message="deleted",
    )


@router.get("/{lesson_id}/description-file")
def get_published_edited_lesson_description_file(
    request: RequestWithFullUser, lesson_id: fields.ObjectIdField = Path(...)
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.READ_UPDATE_LIMITES,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    if not lesson.mid_edit:
        return responses.ApiError(
            code=400,
            message="lesson is not in edit mode",
        )

    description_file = None

    if lesson.edit_data.description_file:
        description_file = lesson.edit_data.description_file
    elif lesson.description_file:
        description_file = lesson.description_file

    if not description_file:
        return responses.ApiError(
            code=404,
            message="description file not found",
        )

    url = GCP_MANAGER.bucket_manager.generate_file_download_url(description_file)

    return responses.ApiSuccess(
        data={
            "url": url,
        }
    )


@router.post(
    "/{lesson_id}/part",
)
def add_part_to_edit_published_lesson(
    request: RequestWithFullUser,
    data: models.AddPartPayload,
    lesson_id: fields.ObjectIdField = Path(...),
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    for part in lesson.edit_data.parts:
        new_order = data.old_parts_order.get(part.id)

        if new_order is None:
            return responses.ApiError(
                code=400,
                message=f"part {part.id} not found in old parts order",
            )
        if new_order < 0:
            return responses.ApiError(
                code=400,
                message=f"part {part.id} has invalid order",
            )

        part.order = new_order

    add_part_res = updates.add_part_to_published_lesson(
        lesson, data.new_part_order, data.part_type
    )

    if add_part_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess(
        data={
            "message": "part added successfully",
            "part_id": add_part_res.value.edit_data.parts[-1].id,
            "part_index": data.new_part_order,
        }
    )


@router.post(
    "/{lesson_id}/parts/order",
)
def edit_parts_order_in_edit_published_lesson(
    request: RequestWithFullUser,
    data: dict[str, int],
    lesson_id: fields.ObjectIdField = Path(...),
):
    update_res = updates.reorder_parts_in_published_lesson(lesson_id, request, data)

    if update_res.failure:
        return responses.ApiError()

    return responses.ApiSuccess(
        message="parts order updated successfully",
    )


@router.delete(
    "/{lesson_id}/part",
)
def delete_part_from_edit_published_lesson(
    request: RequestWithFullUser,
    part_id: str = Query(...),
    lesson_id: fields.ObjectIdField = Path(...),
):
    tran_res = transactions.remove_part_from_published_lesson(
        lesson_id,
        part_id,
        request,
    )

    if not tran_res.success:
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        message="deleted",
    )


@router.get(
    "/{lesson_id}/part/upload-link",
)
def get_file_upload_link(
    request: RequestWithFullUser,
    lesson_id: fields.ObjectIdField = Path(...),
    screen_side: int = Query(..., gt=-1, lt=3),
    part_id: str = Query(...),
    file_type: str = Query(...),
    is_video: bool = Query(default=False),
    is_image: bool = Query(default=False),
):
    if not is_video and not is_image:
        return responses.ApiError(
            code=400,
            message="is_video or is_image must be true",
        )

    mime_type = None

    if is_video:
        mime_type = get_video_mime_type(file_type)
    elif is_image:
        mime_type = get_image_mime_type(file_type)

    if mime_type is None:
        return responses.ApiError(
            code=400,
            message="invalid file type",
        )

    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    part = lesson.edit_data.get_part_by_id(part_id)

    if not part:
        return responses.ApiError(
            code=404,
            message="part not found",
        )

    if not part.is_normal():
        return responses.ApiError(
            code=400,
            message="The provided part can't have a screen",
        )

    upload_path = f"{GCPFoldersNames.LESSON_EDITS}/{lesson_id}/{part_id}/{screen_side}-{time.time()}.{file_type}"

    return responses.ApiSuccess(
        data={
            "upload_link": GCP_MANAGER.bucket_manager.generate_file_upload_url(
                upload_path, mime_type
            ),
            "upload_path": upload_path,
        }
    )


@router.put(
    "/{lesson_id}/part/screen",
)
def update_part_screen_in_edit_lesson_mode(
    request: RequestWithFullUser,
    data: models.UpdatePartDataPayload,
    lesson_id: fields.ObjectIdField = Path(...),
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    part = lesson.edit_data.get_part_by_id(data.part_id)

    if part is None:
        return responses.ApiError(
            code=404,
            message="part not found",
        )

    if not part.is_normal():
        return responses.ApiError(
            code=400,
            message="The provided part can't have a screen",
        )

    mime_type = None

    # if the given screen is a media screen will check if the file exists in the bucket
    if data.media:
        # check if the given url is for the givem draft lesson
        if (
            str(lesson_id) not in data.url
            or not GCPFoldersNames.LESSON_EDITS in data.url
        ):
            return responses.ApiError(
                code=400,
                message="invalid media url",
            )
        # try to get the file from the bucket and its metadata
        try:
            file = GCP_MANAGER.bucket_manager.get_file_blob(data.url)
            file.patch()
        except:
            return responses.ApiError(
                code=400,
                message="invalid media url",
            )

        # set the mime type
        mime_type = file.content_type
    else:
        if not valid_url(data.url):
            return responses.ApiError(message="invalid url")

    screen = part.screens[data.screen]

    screen.mime_type = mime_type
    screen.url = data.url
    screen.type_ = data.type_.value
    screen.comment = data.comment

    tran_res = transactions.update_screen_in_published_lesson(
        lesson_id,
        data.part_id,
        data.screen,
        screen,
    )

    if not tran_res.success:
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        message="updated",
    )


@router.put("/{lesson_id}/part/title")
def update_part_title_in_draft_lesson(
    request: RequestWithFullUser,
    title: str = Query(...),
    part_id: str = Query(...),
    lesson_id: fields.ObjectIdField = Path(...),
):
    lesson_res = updates.update_part_title_in_published_lesson(
        lesson_id,
        part_id,
        title,
        request,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    return responses.ApiSuccess(
        message="updated",
    )


@router.patch("/{lesson_id}")
def submit_edits_to_lessons(
    request: RequestWithFullUser,
    lesson_id: fields.ObjectIdField = Path(...),
):
    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    blobs_to_delete = []
    blobs_to_move = []

    image_and_video_types = [
        ScreensTypes.IMAGE,
        ScreensTypes.VIDEO,
    ]

    # loop through the parts in the edited lesson and build a list of the files to delete and move
    for edited_part in lesson.edit_data.parts:
        # get the current part from the published lesson
        crr_part = lesson.get_part(edited_part.id)

        # if the current part is not found in the published lesson it means that it is a new part
        if crr_part is None:        
            
            if edited_part.gcp_path:
                blobs_to_move.append(edited_part.gcp_path)
                edited_part.gcp_path = (
                    GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
                        edited_part.gcp_path
                    )
                )
            
            for edited_screen in edited_part.screens:
                if edited_screen.type_ in image_and_video_types:
                    # for each new media screen will move the file from the edit folder to the published folder
                    blobs_to_move.append(edited_screen.url)
                    edited_screen.url = (
                        GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
                            edited_screen.url
                        )
                    )
        else:
            if edited_part.is_panoramic():
                if edited_part.gcp_path:
                    if crr_part.gcp_path:
                        blobs_to_delete.append(crr_part.gcp_path)
                    blobs_to_move.append(edited_part.gcp_path)
                    edited_part.gcp_path = (
                        GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
                            edited_part.gcp_path
                        )
                    )
                else:
                    if crr_part.gcp_path:
                        blobs_to_delete.append(crr_part.gcp_path)
                    
            else:
                for index, edited_screen in enumerate(edited_part.screens):
                    edited_screen: LessonScreen
                    crr_screen: LessonScreen = crr_part.screens[index]

                    # if the current screen is a media and the new one is not
                    if (
                        crr_screen.type_ in image_and_video_types
                        and edited_screen.type_ not in image_and_video_types
                    ):
                        blobs_to_delete.append(crr_screen.url)
                    # if the current screen is not a media and the new one is
                    elif (
                        crr_screen.type_ not in image_and_video_types
                        and edited_screen.type_ in image_and_video_types
                    ):
                        blobs_to_move.append(edited_screen.url)
                        edited_screen.url = (
                            GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
                                edited_screen.url
                            )
                        )
                    # if both are media
                    elif (
                        crr_screen.type_ in image_and_video_types
                        and edited_screen.type_ in image_and_video_types
                    ):
                        # if the urls are different
                        if not crr_screen.url == edited_screen.url:
                            blobs_to_delete.append(crr_screen.url)
                            blobs_to_move.append(edited_screen.url)
                            edited_screen.url = (
                                GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
                                    edited_screen.url
                                )
                            )

    # loop through the parts in the published lesson and build a list of the files to delete
    for edited_part in lesson.parts:
        edited_part: LessonPart
        # get the current part from the published lesson
        crr_part = lesson.edit_data.get_part_by_id(edited_part.id)
        # if there is no part with the same id in the edited lesson it means that it is a deleted part
        if crr_part is None:
            for edited_screen in edited_part.screens:
                edited_screen: LessonScreen
                if edited_screen.type_ in image_and_video_types:
                    blobs_to_delete.append(edited_screen.url)

    if lesson.edit_data.thumbnail:
        if lesson.thumbnail:
            blobs_to_delete.append(
                GCP_MANAGER.get_local_gcp_file_path(lesson.thumbnail)
            )
        blobs_to_move.append(
            GCP_MANAGER.get_local_gcp_file_path(lesson.edit_data.thumbnail)
        )

        lesson.thumbnail = GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
            lesson.edit_data.thumbnail
        )

    if lesson.edit_data.description_file:
        if lesson.description_file:
            blobs_to_delete.append(lesson.description_file)
        blobs_to_move.append(lesson.edit_data.description_file)

        lesson.description_file = GCP_MANAGER.rename_gcp_edit_lesson_to_lesson_file(
            lesson.edit_data.description_file
        )

    if lesson.edit_data.title:
        lesson.title = lesson.edit_data.title

    if lesson.edit_data.description:
        lesson.description = lesson.edit_data.description

    if isinstance(lesson.edit_data.categories, list):
        lesson.categories = lesson.edit_data.categories

    if isinstance(lesson.edit_data.credit, str):
        lesson.credit = lesson.edit_data.credit

    # delete the old part
    lesson.parts = lesson.edit_data.parts
    lesson.edit_data = None
    lesson.mid_edit = False

    tran_res = transactions.save_published_lesson_edits(
        lesson, blobs_to_delete, blobs_to_move
    )

    if not tran_res or not tran_res.success:
        return responses.ApiError(
            code=500,
            message="something went wrong while saving the lesson",
        )

    return responses.ApiSuccess(
        message="lesson updated successfully",
    )


@router.patch("/{lesson_id}/current-editor")
def return_lesson_editing_to_initial_editor(
    request: RequestWithFullUser,
    lesson_id: fields.ObjectIdField = Path(...),
):
    res = updates.return_edit_to_initial_editor(lesson_id, request)

    if res.failure:
        if res.not_found:
            return responses.ApiError(
                message="lesson not found",
                code=404,
            )
        return responses.ApiError(
            message="something went wrong while returning the lesson to the initial editor",
            code=500,
        )

    return responses.ApiSuccess(
        message="lesson returned to the initial editor successfully",
    )


@router.put("/{lesson_id}/part/panaromic")
def edit_part_panoramic(
    request: RequestWithFullUser,
    lesson_id: fields.ObjectIdField = Path(...),
    payload: models.UpdatePartPanoramicPayload = Depends(),
):
    if not payload.image and not payload.panoramic_url:
        return responses.ApiError(message="no image or url provided")
    elif payload.image and payload.panoramic_url:
        return responses.ApiError(message="can't provide both image and url")
    
    if payload.image and not payload.image.content_type.startswith("image/"):
        return responses.ApiError(message="invalid image type")

    lesson_res = queries.get_published_lesson_by_id(
        lesson_id,
        request,
        action=Actions.UPDATE,
    )

    if lesson_res.failure:
        if lesson_res.not_found:
            return responses.ApiError(
                code=404,
                message="lesson not found",
            )
        return responses.ApiError(
            code=500,
            message="something went wrong",
        )

    lesson = lesson_res.value

    part = lesson.edit_data.get_part_by_id(payload.part_id)

    if part is None:
        return responses.ApiError(
            code=404,
            message="part not found",
        )

    if not part.is_panoramic():
        return responses.ApiError(
            code=400,
            message="The provided part can't have a panoramic",
        )

    new_panormic_path = None

    if payload.panoramic_url:
        
        res = updates.update_lesson_part_panoramic(
            lesson, request, payload.part_id, "", payload.panoramic_url
        )
    else:
        try:
            new_panormic_path = GCP_MANAGER.upload_lesson_part_panoramic(
                str(lesson.id),
                payload.part_id,
                payload.image.file,
                payload.image.filename,
                payload.image.content_type,
                edit=True,
            )
        except:
            return responses.ApiError(message="error uploading panoramic image")

        res = updates.update_lesson_part_panoramic(lesson, request, payload.part_id, new_panormic_path, "")
    
    if res.failure:
        return responses.ApiError(message="error updating panoramic image")
    
    try:
        GCP_MANAGER.delete_lesson_part_old_panoramic(
            str(lesson.id), payload.part_id, exclude=new_panormic_path, edit=True
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
