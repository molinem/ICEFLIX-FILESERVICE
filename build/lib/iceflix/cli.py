import logging
import sys

from iceflix.file import RunFile


LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

def setup_logging():
    """Configure the logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
    )


def file_service():
    """CLI command."""
    setup_logging()
    logging.info("File service")
    app = RunFile()
    app.main(sys.argv)
    return 0
