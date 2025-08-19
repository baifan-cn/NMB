from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_magazines():
    return {"items": [], "total": 0}
