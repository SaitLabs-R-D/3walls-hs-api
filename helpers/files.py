from typing import Union
import urllib
from io import BytesIO
import mimetypes

# https://mimetype.io/all-types/


def get_video_mime_type(file_extension: str) -> Union[str, None]:

    mime_type, _ = mimetypes.guess_type("video." + file_extension)

    if mime_type is None or "video" not in mime_type:
        return None

    return mime_type


def get_image_mime_type(file_extension: str) -> Union[str, None]:

    mime_type, _ = mimetypes.guess_type("image." + file_extension)

    if mime_type is None or "image" not in mime_type:
        return None

    return mime_type


def decode_base64_image(
    base64_image: str,
) -> Union[tuple[BytesIO, str], tuple[None, None]]:

    try:
        response = urllib.request.urlopen(base64_image)
        file = BytesIO(response.file.read())

        content_type = response.headers["Content-Type"]

        if "image" not in content_type:
            return None, None

        return file, content_type
    except Exception:
        return None, None


def get_file_extension_from_mime_type(file_name: str) -> Union[str, None]:

    try:
        return mimetypes.guess_extension(file_name).replace(".", "", 1)
    except Exception:
        return None


def decode_base64_pdf(
    base64_file: str,
) -> Union[tuple[BytesIO, str], tuple[None, None]]:

    try:
        response = urllib.request.urlopen(base64_file)
        file = BytesIO(response.file.read())

        content_type = response.headers["Content-Type"]

        if "pdf" not in content_type:
            return None, None

        return file, content_type
    except Exception:
        return None, None


def varify_image_content_type(
    content_type: str,
    allow_svg: bool = False,
) -> bool:

    if "image" not in content_type:
        return False

    if not allow_svg and "svg" in content_type:
        return False

    return True


def varify_video_content_type(
    content_type: str,
) -> bool:

    if "video" not in content_type:
        return False

    return True


def varify_document_content_type(
    content_type: str,
) -> bool:

    allowd_document_types = ["application/pdf"]

    return content_type in allowd_document_types
