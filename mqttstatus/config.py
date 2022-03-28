import argparse
import pathlib
import yaml

from mqttstatus.log import logger


class MQTTStatusConfig(dict):

    def __init__(self, args):

        super().__init__()

        self._parse_cli_args(args)
        self._parse_file(self['config'])

    def _parse_cli_args(self, args: list[str]):
        parser = argparse.ArgumentParser()

        # CLI Options
        parser.add_argument('-c', '--config', type=pathlib.Path, default=pathlib.Path('./conf/mqttstatus.yaml'))
        parser.add_argument('-v', '--verbose', action='store_true', default=None)

        # General Options
        parser.add_argument('--host', type=str)
        parser.add_argument('--port', type=str, default=1883)
        parser.add_argument('-x', '--prefix', type=str)
        parser.add_argument('-t', '--topic', type=str)
        parser.add_argument('-i', '--interval', type=int, default=5)
        parser.add_argument('-u', '--username', type=str)
        parser.add_argument('-p', '--password', type=str)

        parsed_args = parser.parse_args(args)

        self.update({
            'config': parsed_args.config,
            'verbose': parsed_args.verbose,
            'mqtt_host': parsed_args.host,
            'mqtt_port': parsed_args.port,
            'prefix': parsed_args.prefix,
            'topic': parsed_args.topic,
            'interval': parsed_args.interval,
            'username': parsed_args.username,
            'password': parsed_args.password,
        })

    def _parse_file(self, path: str):
        try:
            with open(path, 'r') as file:
                config_file = yaml.load(file, Loader=yaml.FullLoader)
                if config_file is None:
                    return
                for key in config_file:
                    if key not in self or self[key] is None:
                        self[key] = config_file[key]
                logger.debug("Config file loaded")
        except yaml.scanner.ScannerError:
            logger.error("Invalid config format")
        except FileNotFoundError:
            logger.error("Could not locate config file")

    @property
    def verbose(self) -> bool:
        return self['verbose']

    @property
    def host(self) -> str:
        return self['mqtt_host']

    @property
    def port(self) -> int:
        return self['mqtt_port']

    @property
    def prefix(self) -> str:
        return self['prefix']

    @property
    def topic(self) -> str:
        return self['topic']

    @property
    def interval(self) -> str:
        return self['interval']

    @property
    def username(self) -> str:
        return self['username']

    @property
    def password(self) -> str:
        return self['password']
