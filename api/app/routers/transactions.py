from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import CurrentUser, get_current_user

# すべてのエンドポイントで認証を必須にする。中身は Issue #12、#13 で実装する
router = APIRouter(prefix="/api/transactions", tags=["transactions"], dependencies=[Depends(get_current_user)])


def _not_implemented() -> HTTPException:
    return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


@router.get("")
def list_transactions(user: CurrentUser = Depends(get_current_user)) -> None:
    raise _not_implemented()


@router.post("")
def create_transaction(user: CurrentUser = Depends(get_current_user)) -> None:
    raise _not_implemented()


@router.put("/{transaction_id}")
def update_transaction(transaction_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    raise _not_implemented()


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, user: CurrentUser = Depends(get_current_user)) -> None:
    raise _not_implemented()
