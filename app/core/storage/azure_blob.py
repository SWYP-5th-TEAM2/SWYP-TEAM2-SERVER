import asyncio
import uuid

from azure.core.exceptions import (
    AzureError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions.image import (
    StorageServerConnectionFailedException,
    StorageServerUploadFailedException,
)


class AzureBlobStorage:
    def __init__(self) -> None:
        self.connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_storage_container_name

    async def upload_image(
        self,
        file: UploadFile,
        image_purpose: str,
        user_id: str,
        content_type: str,
    ) -> tuple[str, str]:
        # 서비스 계층에서 확인한 실제 MIME 타입으로 확장자를 결정
        extension = self._get_extension(content_type)

        # 용도와 사용자별로 경로를 분리, UUID로 중복 방지
        blob_name = f"{image_purpose.lower()}/{user_id}/{uuid.uuid4()}{extension}"

        try:
            # Azure Blob SDK는 동기 방식이므로 별도 스레드에서 실행
            blob_name, image_url = await asyncio.to_thread(
                self._upload_image,
                file,
                blob_name,
                content_type,
            )
            return blob_name, image_url

        except (ServiceRequestError, ValueError):
            raise StorageServerConnectionFailedException()
        except AzureError:
            raise StorageServerUploadFailedException()

    def _upload_image(
        self,
        file: UploadFile,
        blob_name: str,
        content_type: str,
    ) -> tuple[str, str]:
        with BlobServiceClient.from_connection_string(
            self.connection_string,
        ) as blob_service_client:
            blob_client = blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )

            file.file.seek(0)

            blob_client.upload_blob(
                data=file.file,
                overwrite=False,
                content_settings=ContentSettings(content_type=content_type),
            )
            return blob_name, blob_client.url

    async def delete_image(self, blob_name: str) -> None:
        try:
            # DB 저장 실패 시 업로드된 Blob을 정리
            await asyncio.to_thread(
                self._delete_image,
                blob_name,
            )
        except ResourceNotFoundError:
            # 이미 삭제되었거나 존재하지 않는 Blob은 정리가 완료된 것으로 간주
            return
        except (ServiceRequestError, ValueError):
            raise StorageServerConnectionFailedException()
        except AzureError:
            raise StorageServerUploadFailedException()

    def _delete_image(self, blob_name: str) -> None:
        with BlobServiceClient.from_connection_string(
            self.connection_string,
        ) as blob_service_client:
            blob_client = blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            blob_client.delete_blob(delete_snapshots="include")

    def _get_extension(self, content_type: str) -> str:
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        return extensions[content_type]
