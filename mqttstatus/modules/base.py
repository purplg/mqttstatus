import abc
from threading import Thread
from mqttstatus.log import logger

class Module(abc.ABC):

    def start(self):
        logger.info(f"Starting module: '{self.__class__.__name__}'")

        self._thread = Thread(target=self.run, daemon=True)
        self._thread.start()

    def run(self):
        pass

    def on_mqtt(self, cmd, payload):
        pass
