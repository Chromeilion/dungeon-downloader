import logging
import os
from importlib.metadata import version

from dotenv import load_dotenv

import dungeondownloader.cli


def set_loglevel():
    """
    Set the log level based on the DUNGEONDOWNLOADER_LOGLEVEL env
    variable. Supports a .env file and defaults to 'INFO'.
    """
    load_dotenv()
    logging.basicConfig(
        format='%(levelname)s:%(message)s',
        level=getattr(
            logging,
            os.environ.get("DUNGEONDOWNLOADER_LOGLEVEL", "INFO")
        )
    )


def main():
    """Script Entrypoint. Sets loglevel and runs the CLI.
    """
    set_loglevel()
    logging.info(f"Running dungeon downloader version "
                 f"{version('dungeon-downloader')}")
    logging.info("This is a fan made program and uses an undocumented API, "
                 "use at your own risk")
    dungeondownloader.cli.main()
    logging.info("Run complete, exiting")


if __name__ == "__main__":
    main()
