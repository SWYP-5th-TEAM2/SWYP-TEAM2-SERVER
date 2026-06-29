import uuid
from pathlib import Path

from azure.core.exceptions import ServiceRequestError, AzureError
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions.image import StorageServerConnectionFailedException, StorageServerUploadFailedException


class AzureBlobStorage:
    def __init__(self) -> None:
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.container_name = settings.azure_storage_container_name
        self.account_name = settings.azure_storage_account_name

    async def upload_image(
        self,
        file: UploadFile,
        image_purpose: str,
        user_id: str,
    ) -> tuple[str, str]:
        extension = self._get_extension(file.filename)

        blob_name = f"{image_purpose.lower()}/{user_id}/{uuid.uuid4()}{extension}"

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)

            file.file.seek(0)

            container_client.upload_blob(
                name=blob_name,
                data=file.file,
                overwrite=False,
                content_settings=ContentSettings(content_type=file.content_type),
            )

            image_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

            return blob_name, image_url

        except ServiceRequestError:
            raise StorageServerConnectionFailedException()
        except AzureError:
            raise StorageServerUploadFailedException()


    def _get_extension(self, filename: str | None) -> str:
        if not filename:
            return ""

        return Path(filename).suffix.lower()
