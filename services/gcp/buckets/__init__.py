from io import BytesIO
from datetime import timedelta
from google.cloud.storage import Blob, Bucket
from helpers.env import EnvVars
from google.auth import compute_engine
from typing import Optional, Literal
from google.auth.transport import requests
from google.auth.exceptions import TransportError


class BucketManager:
    def __init__(
        self, bucket: Bucket, credentials: Optional[compute_engine.Credentials]
    ) -> None:
        self.bucket = bucket

        # configre the bucket cors
        self.bucket.cors = [
            {
                "origin": EnvVars.BUCKET_ALLOWED_ORIGINS.split(","),
                "method": ["GET", "PUT"],
                "responseHeader": ["*"],
                "maxAgeSeconds": 3600,
            }
        ]
        self.bucket.patch()

        self.credentials = credentials

    def _signed_url_creator(
        self,
        filename: str,
        expiration: timedelta,
        method: Literal["PUT", "GET"],
        content_type: str = None,
        counter: int = 0,
    ):
        kwargs = {}
        if not EnvVars.IS_LOCAL:
            if self.credentials.token is None:
                print("refreshing token")
                # Perform a refresh request to populate the access token of the
                # current credentials.
                self.credentials.refresh(requests.Request())
            kwargs["service_account_email"] = self.credentials.service_account_email
            kwargs["access_token"] = self.credentials.token

        if content_type:
            kwargs["content_type"] = content_type

        blob = self.bucket.blob(filename)
        try:
            return blob.generate_signed_url(
                version="v4", expiration=expiration, method=method, **kwargs
            )
        except TransportError as e:
            if EnvVars.IS_LOCAL:
                raise e

            if counter > 3:
                raise e
            self.credentials.token = None
            return self._signed_url_creator(
                filename, expiration, method, content_type, counter + 1
            )

    def generate_file_upload_url(
        self,
        filename: str,
        content_type: str,
        expiration: timedelta = timedelta(hours=6),
    ):
        """
        generate a signed url for uploading a file to the storage bucket for a limited time
        """
        return self._signed_url_creator(filename, expiration, "PUT", content_type)

    def generate_file_download_url(
        self, filename: str, expiration: timedelta = timedelta(hours=1)
    ):
        """
        generate a signed url for downloading a file from the storage bucket for a limited time
        """
        return self._signed_url_creator(filename, expiration, "GET")

    def generate_link_for_open_file(self, filename: str):
        """
        generate a public link for opening a file from the storage bucket
        the file needs to be public
        """
        return f"https://storage.googleapis.com/{self.bucket.name}/{filename}"

    def upload_file_from_bytes(
        self, file: BytesIO, filename: str, content_type: str, public: bool = False
    ):
        """
        upload a file to the storage bucket from a bytes object
        """
        blob = self.bucket.blob(filename)

        blob.upload_from_file(file, content_type=content_type)

        if public:
            blob.make_public()

    def get_file_blob(self, path: str):
        """
        get a blob object for a file from the storage bucket
        """
        return self.bucket.blob(path)

    def duplicate_folder(self, source_folder_name: str, destination_folder_name: str):
        """
        duplicate a folder in the storage bucket
        """

        blobs: list[Blob] = self.bucket.list_blobs(prefix=source_folder_name)

        for blob in blobs:
            # the list_blobs method returns the source folder as well
            if not blob.name == source_folder_name:
                new_name = blob.name.replace(
                    source_folder_name, destination_folder_name
                )
                # copy the new blob to the destination folder and save the acl if it has one
                new_bucket = self.bucket.copy_blob(blob, self.bucket, new_name)
                if blob.acl:
                    new_bucket.acl.save(blob.acl)

    def delete_blobs_by_prefix(self, prefix: str):
        """
        delete all blobs in the storage bucket by a prefix
        """
        blobs: list[Blob] = list(self.bucket.list_blobs(prefix=prefix))

        if blobs:
            self.bucket.delete_blobs(blobs)
    