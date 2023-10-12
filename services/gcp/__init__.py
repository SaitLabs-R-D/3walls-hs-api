from google.cloud import storage
from .buckets import BucketManager
from helpers.env import EnvVars
from io import BytesIO
import time, urllib
from .types import FoldersNames
from google.cloud.storage import Blob
import google.auth

import urllib

import google.auth.transport.requests
import google.oauth2.id_token


def make_authorized_get_request(endpoint, audience):
    """
    make_authorized_get_request makes a GET request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    using the specified audience value.
    """

    # Cloud Run uses your service's hostname as the `audience` value
    # audience = 'https://my-cloud-run-service.run.app/'
    # For Cloud Run, `endpoint` is the URL (hostname + path) receiving the request
    # endpoint = 'https://my-cloud-run-service.run.app/my/awesome/url'

    req = urllib.request.Request(endpoint)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)

    return response.read()


class GCPManager:
    def __init__(self) -> None:
        self.storage_client = storage.Client()

        creadentials, _ = google.auth.default()

        self.bucket_manager = BucketManager(
            self.storage_client.get_bucket(EnvVars.BUCKET_NAME), creadentials
        )

    def upload_account_logo(
        self, file: BytesIO, account_id: str, file_type: str, content_type: str
    ):
        """
        upload a lesson thumbnail to the storage bucket for a given lesson, returns the public link
        """
        filename = (
            f"{FoldersNames.ACCOUNTS}/{account_id}/logo-{time.time()}.{file_type}"
        )

        self.bucket_manager.upload_file_from_bytes(file, filename, content_type, True)

        return self.bucket_manager.generate_link_for_open_file(filename)

    def delete_account_logo(self, account_id: str):
        """
        delete the account logo
        """
        filename = f"{FoldersNames.ACCOUNTS}/{account_id}/logo-*"

        self.bucket_manager.delete_blobs_by_prefix(filename)

    def upload_lesson_thumbnail(
        self,
        file: BytesIO,
        lesson_id: str,
        file_type: str,
        content_type: str,
        edit: bool = False,
    ):
        """
        upload a lesson thumbnail to the storage bucket for a given lesson, returns the public link
        params:
            file: the file to upload
            lesson_id: the id of the lesson
            file_type: the type of the file
            content_type: the content type of the file
            edit: if to upload to the edit folder
        """

        filename = (
            f"{FoldersNames.LESSONS}/{lesson_id}/thumbnail-{time.time()}.{file_type}"
        )

        if edit:
            filename = f"{FoldersNames.LESSON_EDITS}/{lesson_id}/thumbnail-{time.time()}.{file_type}"

        self.delete_lesson_old_thumbnail(lesson_id)

        self.bucket_manager.upload_file_from_bytes(file, filename, content_type, True)

        return self.bucket_manager.generate_link_for_open_file(filename)

    def upload_lesson_description_file(
        self, file: BytesIO, lesson_id: str, edit: bool = False
    ):
        """
        upload a lesson description file to the storage bucket for a given lesson, returns the public link
        """
        file_type = "pdf"
        content_type = "application/pdf"

        filename = f"{FoldersNames.LESSONS}/{lesson_id}/description-file.{file_type}"

        if edit:
            filename = (
                f"{FoldersNames.LESSON_EDITS}/{lesson_id}/description-file.{file_type}"
            )

        self.bucket_manager.upload_file_from_bytes(file, filename, content_type, False)

        return filename

    def delete_lesson_part(self, lesson_id: str, part_id: str, edit: bool = False):
        """
        delete a lesson part from the storage bucket
        """
        if edit:
            prefix = f"{FoldersNames.LESSON_EDITS}/{lesson_id}/{part_id}/"
        else:
            prefix = f"{FoldersNames.LESSONS}/{lesson_id}/{part_id}/"

        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=prefix
        )

        blobs = list(blobs)

        self.bucket_manager.bucket.delete_blobs(blobs)

    def delete_lesson(self, lesson_id: str):
        """
        delete a lesson from the storage bucket
        """
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=f"{FoldersNames.LESSONS}/{lesson_id}"
        )

        blobs_ = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.LESSON_EDITS}/{lesson_id}",
        )

        blobs = list(blobs) + list(blobs_)

        self.bucket_manager.bucket.delete_blobs(blobs)

    def delete_lesson_old_thumbnail(self, lesson_id: str):
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.LESSONS}/{lesson_id}/thumbnail-",
        )

        self.bucket_manager.bucket.delete_blobs(list(blobs))

    def delete_part_screen_old_media(
        self, lesson_id: str, part_id: str, screen: int, keep: str, edit: bool = False
    ):
        """
        delete old media files for a part screen after a new media file is uploaded pass it the new media file name to keep if nothing is passed it will delete all the old media files
        and if the name does not match any of the old media files it will delete all the old media files
        """
        if edit:
            prefix = f"{FoldersNames.LESSON_EDITS}/{lesson_id}/{part_id}/{screen}-"
        else:
            prefix = f"{FoldersNames.LESSONS}/{lesson_id}/{part_id}/{screen}-"

        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=prefix
        )

        blobs = list(blobs)

        if keep:
            blobs = [blob for blob in blobs if not blob.name == keep]

        self.bucket_manager.bucket.delete_blobs(blobs)

    def duplicate_lesson(self, lesson_id: str, new_lesson_id: str):
        """
        duplicate a lesson in the storage bucket
        """
        self.bucket_manager.duplicate_folder(
            f"{FoldersNames.LESSONS}/{lesson_id}",
            f"{FoldersNames.LESSONS}/{new_lesson_id}",
        )

    def delete_lesson_edit_folder(self, lesson_id: str):
        """
        delete a lesson edit folder from the storage bucket
        """

        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.LESSON_EDITS}/{lesson_id}",
        )

        blobs = list(blobs)

        self.bucket_manager.bucket.delete_blobs(blobs)

    def delete_list_of_lessons_files(self, lesson_id: str, files: list[str]):
        """
        delete a list of files from a lesson folder
        """
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=f"{FoldersNames.LESSONS}/{lesson_id}"
        )

        blobs_ = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.LESSON_EDITS}/{lesson_id}",
        )

        blobs = list(blobs) + list(blobs_)

        blobs = [blob for blob in blobs if blob.name in files]

        self.bucket_manager.bucket.delete_blobs(blobs)

    def move_edit_files_to_publish_folder(self, lesson_id: str, files: list[str]):
        # rename a folder in the storage bucket

        folder_to_rename = f"{FoldersNames.LESSON_EDITS}/{lesson_id}"

        new_folder_name = f"{FoldersNames.LESSONS}/{lesson_id}"

        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=folder_to_rename
        )

        blobs = list(blobs)

        for blob in blobs:
            blob: Blob
            if blob.name in files:
                new_name = blob.name.replace(folder_to_rename, new_folder_name, 1)
                was_public = "READER" in blob.acl.all().get_roles()
                new_blob = self.bucket_manager.bucket.copy_blob(
                    blob, self.bucket_manager.bucket, new_name, preserve_acl=True
                )
                if was_public:
                    new_blob.make_public()
                blob.delete()

        self.delete_lesson_edit_folder(lesson_id)

    def delete_account_folder(self, account_id: str):
        """
        delete an account folder from the storage bucket
        """

        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket, prefix=f"{FoldersNames.ACCOUNTS}/{account_id}"
        )

        blobs = list(blobs)

        self.bucket_manager.bucket.delete_blobs(blobs)

    def upload_site_help_background_image(
        self,
        file: BytesIO,
        help_id: str,
        file_type: str,
        content_type: str,
    ):
        filename = f"{FoldersNames.SITE_HELP}/{help_id}/background-image-{time.time()}.{file_type}"

        self.delete_site_help_old_background_image(help_id)

        self.bucket_manager.upload_file_from_bytes(file, filename, content_type, True)

        return self.bucket_manager.generate_link_for_open_file(filename)

    def delete_site_help_old_background_image(self, help_id: str):
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.SITE_HELP}/{help_id}/background-image-",
        )

        self.bucket_manager.bucket.delete_blobs(list(blobs))

    def upload_site_help_pdf(self, file: BytesIO, help_id: str):
        filename = f"{FoldersNames.SITE_HELP}/{help_id}/pdf.pdf"

        self.bucket_manager.upload_file_from_bytes(
            file, filename, "application/pdf", False
        )

        return filename

    def delete_site_help_pdf(self, help_id: str):
        self.bucket_manager.bucket.delete_blob(
            blob_name=f"{FoldersNames.SITE_HELP}/{help_id}/pdf.pdf"
        )

    def delete_site_help_folder(self, help_id: str):
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=f"{FoldersNames.SITE_HELP}/{help_id}",
        )

        self.bucket_manager.bucket.delete_blobs(list(blobs))

    @staticmethod
    def rename_gcp_edit_lesson_to_lesson_file(name: str) -> str:
        new_name = name.replace(FoldersNames.LESSON_EDITS, FoldersNames.LESSONS, 1)

        return new_name

    @staticmethod
    def get_local_gcp_file_path(name: str) -> str:
        name = name.split(
            f"{EnvVars.BUCKET_NAME}/",
            1,
        )

        return name[1]

    def upload_lesson_part_panoramic(
        self,
        lesson_id: str,
        part_id: str,
        file: BytesIO,
        filename: str,
        content_type: str,
        edit: bool = False,
    ) -> str:
        """
        upload a panoramic image to the storage bucket
        """

        file_type = filename.split(".")[-1]

        upload_path = f"{FoldersNames.LESSONS}/{lesson_id}/{part_id}/panoramic-{time.time()}.{file_type}"

        if edit:
            upload_path = f"{FoldersNames.LESSON_EDITS}/{lesson_id}/{part_id}/panoramic-{time.time()}.{file_type}"
        
        self.bucket_manager.upload_file_from_bytes(
            file, upload_path, content_type, False
        )

        return upload_path

    def delete_lesson_part_old_panoramic(
        self, lesson_id: str, part_id: str, exclude: str = None, edit: bool = False
    ):
        """
        delete the old panoramic image from the storage bucket
        """
        
        prefix = f"{FoldersNames.LESSONS}/{lesson_id}/{part_id}/panoramic-"
        
        if edit:
            prefix = f"{FoldersNames.LESSON_EDITS}/{lesson_id}/{part_id}/panoramic-"
        
        blobs = self.storage_client.list_blobs(
            self.bucket_manager.bucket,
            prefix=prefix,
        )

        blobs = list(blobs)
        
        if exclude:
            blobs = [blob for blob in blobs if not blob.name == exclude]

        if not blobs:
            return
        
        self.bucket_manager.bucket.delete_blobs(blobs)


GCP_MANAGER = GCPManager()
