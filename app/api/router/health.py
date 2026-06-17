from fastapi import APIRouter
from sqlalchemy import text

from app.core.dependencies import DbSession
from app.core.responses import success_response

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check() -> dict:
    return success_response(
        message="서버 정상 동작",
        data={"status": "ok"},
    )


@router.get("/db")
def db_health_check(db: DbSession) -> dict:
    db.execute(text("SELECT 1"))
    return success_response(
        message="DB 연결 정상",
        data={"database": "ok"},
    )
