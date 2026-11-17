from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/summary", tags=["summary"], dependencies=[Depends(get_current_user)])


@router.get("/monthly")
def monthly_summary(user: CurrentUser = Depends(get_current_user)) -> None:
    # Issue #14 で実装する
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
