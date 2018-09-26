import abc
import typing

T = typing.TypeVar("T")


class AbstractModalTrueFalseDefaultQuestionUI(object):
    """A UI for asking a True, False, Cancel question modally, with a declared default option of either T or F."""

    @abc.abstractmethod
    async def execute(self, question: str, tname: str = "Y", fname: str = "N", cname: str = "C",
                      default: bool = False) -> bool:
        """Override this, ask the question and wait for an answer.  Throw CancelledError on cancel."""
        raise NotImplementedError()
