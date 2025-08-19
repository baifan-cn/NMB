from fastapi import APIRouter

router = APIRouter()


@router.get("/current")
async def get_current_membership():
    return {"status": "ok", "membership": None}
