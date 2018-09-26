import fieui.FeedbackUI


class ShellFeedbackUI(fieui.FeedbackUI.AbstractFeedbackUI):
    _shell = None
    _tracebackWarning = False

    def __init__(self, shell: "Shell", tracebackWarning: bool = False):
        self._shell = shell
        self._tracebackWarning = tracebackWarning
        super().__init__()

    async def error(self, message: str):
        m = self._shell.colorize(message, 'red')
        self._shell.perror(m, traceback_war=self._tracebackWarning)

    async def warn(self, message: str):
        m = self._shell.colorize("Warning: " + message, 'yellow')
        self._shell.pfeedback(m)

    async def output(self, message: str):
        self._shell.poutput(message)

    async def feedback(self, message: str):
        self._shell.pfeedback(message)

    async def paged_output(self, data: str):
        self._shell.ppaged(data)
