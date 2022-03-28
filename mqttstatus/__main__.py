import signal
import sys

from mqttstatus.agent import MQTTAgent
from mqttstatus.config import MQTTStatusConfig


def main(config: MQTTStatusConfig):
    agent = MQTTAgent(config.host, config.port, config.username, config.password, config.prefix, config.topic, config.interval)
    signal.signal(signal.SIGINT, agent.stop)
    signal.signal(signal.SIGTERM, agent.stop)
    agent.run()


if __name__ == "__main__":
    config = MQTTStatusConfig(sys.argv[1:])

    from mqttstatus.log import setup_logging

    setup_logging(verbose=config.verbose)

    main(config)
