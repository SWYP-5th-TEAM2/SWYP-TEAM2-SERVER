from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.services.common.image_service import upload_image

router = APIRouter()


@router.post(
    "/image",
    summary="이미지 업로드",
    description="이미지 파일 업로드 시 Azure Blob Storage과 Image 테이블 저장 후 id 및 url 반환",
)
async def upload_image_file(
    image_purpose: str | None = Form(default=None, alias="imagePurpose"),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    image = await upload_image(
        db=db,
        user_id=user_id,
        file=file,
        image_purpose=image_purpose,
    )

    return success_response(
        data=image,
        message="이미지 업로드 성공",
    )
