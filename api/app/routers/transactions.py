from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth import get_current_user
from app.repository import TransactionRepository, get_repository
from app.schemas import Month, Transaction, TransactionCreated, TransactionInput

# すべてのエンドポイントで認証を必須にする。データアクセスは必ずリポジトリを通す(user_id はそこで付く)
router = APIRouter(prefix="/api/transactions", tags=["transactions"], dependencies=[Depends(get_current_user)])


def _not_found() -> HTTPException:
    # 他人の取引も 404 にして、存在を漏らさない(A3)
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


@router.get("", response_model=list[Transaction])
def list_transactions(
    month: Month | None = Query(default=None),
    repo: TransactionRepository = Depends(get_repository),
) -> list[Transaction]:
    return repo.list(month)


@router.post("", response_model=TransactionCreated, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionInput, repo: TransactionRepository = Depends(get_repository)) -> Transaction:
    return repo.create(body)


@router.put("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: str, body: TransactionInput, repo: TransactionRepository = Depends(get_repository)
) -> Transaction:
    updated = repo.update(transaction_id, body)
    if updated is None:
        raise _not_found()
    return updated


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: str, repo: TransactionRepository = Depends(get_repository)) -> Response:
    if not repo.delete(transaction_id):
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
