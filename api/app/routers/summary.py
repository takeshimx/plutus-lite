from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.repository import TransactionRepository, get_repository
from app.schemas import MonthlySummary

router = APIRouter(prefix="/api/summary", tags=["summary"], dependencies=[Depends(get_current_user)])


@router.get("/monthly", response_model=list[MonthlySummary])
def monthly_summary(repo: TransactionRepository = Depends(get_repository)) -> list[MonthlySummary]:
    return repo.monthly_summary()
