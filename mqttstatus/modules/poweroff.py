import os

from .base import Module


class Poweroff(Module):
    def on_mqtt(self, cmd: str, payload: str) -> None:
        if "power" == cmd and "OFF" == payload:
            os.system("systemctl poweroff")
