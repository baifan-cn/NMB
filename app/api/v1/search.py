from fastapi import APIRouter

router = APIRouter()


@router.get("/magazines")
async def search_magazines(q: str | None = None):
    return {"items": [], "query": q}
