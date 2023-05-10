import signal
import sys

from mqttstatus.agent import MQTTAgent
from mqttstatus.config import MQTTStatusConfig
from mqttstatus.log import setup_logging


def main():
    config = MQTTStatusConfig(sys.argv[1:])

    setup_logging(verbose=config.verbose)

    agent = MQTTAgent(
        config.host,
        config.port,
        config.username,
        config.password,
        config.prefix,
        config.topic,
        config.interval,
    )

    def exit(_signum, _frame):
        agent.stop()

    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    agent.run()
