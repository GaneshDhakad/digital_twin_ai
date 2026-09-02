from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations Engine"],
)

@router.get("/status")
def recommendation_status(current_user: User = Depends(get_current_user)):
    return {"status": "Recommendation Engine active", "user_id": current_user.user_id}
