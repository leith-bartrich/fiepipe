import abc


class AbstractModalTrueFalseQuestionUI(object):
    """A UI for asking a True, False, Cancel question modally (blocking)."""

    @abc.abstractmethod
    async def execute(self, question: str, tname: str = "Y", fname: str = "N", cname: str = "C") -> bool:
        """Override this, ask the question and wait for an answer.  Raise CancelledError on cancel."""
        raise NotImplementedError()
