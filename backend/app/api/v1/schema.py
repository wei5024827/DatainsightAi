from fastapi import APIRouter
import logging
from app.core.schema_service import (
    get_full_schema as load_full_schema,
)

logger = logging.getLogger(__name__)


# 功能：返回数据库的完整 Schem
router = APIRouter(
    prefix="/schema", tags=["Schema"]
)


@router.get("/")
def get_full_schema() -> dict:
    return load_full_schema()
