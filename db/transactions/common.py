from typing import Callable, Optional, Any, TypeVar, Generic
from pydantic import BaseModel, Field
from pymongo.client_session import ClientSession
from db import mongo_client

T = TypeVar("T")


class TransactionResult(BaseModel, Generic[T]):
    success: bool = Field(..., description="Whether the transaction was successful")
    message: Optional[str] = Field(
        None, description="A message describing the result of the transaction"
    )
    value: Optional[T] = Field(None, description="The value of the transaction")


class Transaction(BaseModel):
    func: Callable[[ClientSession, Any], TransactionResult] = Field(
        ..., description="The function to execute"
    )
    args: list = Field(..., description="The function arguments")
    kwargs: dict = Field(..., description="The function keyword arguments")
    success: bool = Field(False, description="Whether the transaction was successful")
    result: Optional[TransactionResult] = Field(None)

    def start(self, session_kwargs: dict = {}, transaction_kwargs: dict = {}):
        with mongo_client.start_session(**session_kwargs) as session:
            with session.start_transaction(**transaction_kwargs):
                res = self.func(session, *self.args, **self.kwargs)

                if not res.success:
                    session.abort_transaction()
                    # TODO log error

            self.result = res
