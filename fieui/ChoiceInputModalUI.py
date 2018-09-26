import abc
import typing

T = typing.TypeVar("T")


class AbstractChoiceInputModalUI(typing.Generic[T]):

    @abc.abstractmethod
    async def execute(self, question: str, choices: typing.Dict[str,T]) -> typing.Tuple[str, T]:
        """Asking routine.  Throw CancelledError as appropriate."""
        raise NotImplementedError()
