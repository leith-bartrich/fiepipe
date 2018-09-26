import abc
import typing

T = typing.TypeVar("T")


class AbstractInputModalUI(typing.Generic[T]):

    @abc.abstractmethod
    def validate(self, v: str) -> typing.Tuple[bool, T]:
        """Validates the string input.  Parses it to type T and indicates if the parsing was succesful and theresponse,
        is valid, via the tuple."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def execute(self, question: str) -> T:
        """Asking routine.  Throw CancelledError as appropriate."""
        raise NotImplementedError()

