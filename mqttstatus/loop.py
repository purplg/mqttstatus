import threading


class TimerLoop:
    """
    Calls the `handler` function ever `interval` seconds
    """

    def __init__(self, interval, handler):
        self.interval = interval
        self.handler = handler
        self.thread = threading.Timer(self.interval, self._tick)

    def _tick(self):
        self.handler()
        self.thread = threading.Timer(self.interval, self._tick)
        self.thread.start()

    def start(self):
        """
        Start the loop
        """
        self.handler()
        self.thread.start()

    def cancel(self):
        """
        Cancel the loop
        """
        self.thread.cancel()
