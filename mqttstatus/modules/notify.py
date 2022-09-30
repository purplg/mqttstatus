import json
import os

from .base import Module
from mqttstatus.log import logger

class Notify(Module):

    def on_mqtt(self, cmd: str, payload: str) -> None:
        if "notify" != cmd:
            return

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing notify json: {e}")
            return

        body = data.get('body')
        if body is None:
            logger.warning(f"Received notification message missing body: {data}")
            return

        time = data.get('time', 5000)
        urgency = data.get('urgency', 'low')
        transient = data.get('transient', False)

        sh = f"notify-send --expire-time={time} --urgency={urgency} \"{body}\""
        if transient:
            sh += " --transient"

        if os.system(sh) > 0:
            logger.warning(f"Error running command: {sh}")
