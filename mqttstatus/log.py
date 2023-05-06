import logging
import logging.handlers
import sys

logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    log_fmt_debug = logging.Formatter(
        "%(levelname)-8s %(asctime)s [%(module)s.%(funcName)s:%(lineno)s]:%(message)s"
    )
    log_fmt = log_fmt_debug if verbose else logging.Formatter("%(message)s")

    file_handler = logging.handlers.RotatingFileHandler("mqttstatus.log")
    stderr_handler = logging.StreamHandler(stream=sys.stderr)

    file_handler.setFormatter(log_fmt_debug)
    stderr_handler.setFormatter(log_fmt)

    logger.setLevel(level=logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)
