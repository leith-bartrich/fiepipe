import abc
import typing

T = typing.TypeVar("T")


class AbstractInputDefaultModalUI(typing.Generic[T]):
    """
    A generic string input modal UI routine with validation and default input.
    """

    @abc.abstractmethod
    def validate(self, v: T) -> typing.Tuple[bool, T]:
        """validates and parses the input.  Returns a tuple[bool,T] which indicates validity and a parsed value if
        valid."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def execute(self, question: str, default: str) -> T:
        """Execute the ask routine.  Throw CancellationError as needed."""
        raise NotImplementedError()
