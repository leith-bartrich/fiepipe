import abc
import typing
from enum import Enum

T = typing.TypeVar("T", bound=Enum)


class AbstractEnumChoiceModal(typing.Generic[T], abc.ABC):

    @abc.abstractmethod
    async def execute(self, question: str) -> T:
        """Asking routine.  Throw CancelledError as appropriate."""
        raise NotImplementedError()
