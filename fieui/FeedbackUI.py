import abc


class AbstractFeedbackUI(object):
    """A UI for simple text feedback.
    All feedback calls are blocking.
    Though with the exception of the PagedOutput,
    they are assumed to be VERY fast.
    """

    @abc.abstractmethod
    async def warn(self, message: str):
        """Prints warning information.  Yellow if possible."""
        raise NotImplementedError()

    async def error(self, message: str):
        """Prints error information.  Red if possible."""
        raise NotImplementedError()

    async def output(self, message: str):
        """Prints important output information.  Black or white if possible."""
        raise NotImplementedError()

    async def feedback(self, message: str):
        """Prints feedback information.  Black or white if possible.  May be filtered when being asked to be less
        verbose. """
        raise NotImplementedError()

    async def paged_output(self, data: str):
        """Prints paged or long-form content the best way it can for the given UI."""
        raise NotImplementedError()
