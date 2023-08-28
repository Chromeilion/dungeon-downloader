import logging
import os
from importlib.metadata import version

from dotenv import load_dotenv

import dungeondownloader.cli


def set_loglevel():
    load_dotenv()
    logging.basicConfig(
        format='%(levelname)s:%(message)s',
        level=getattr(
            logging,
            os.environ.get("DUNGEONDOWNLOADER_LOGLEVEL", "INFO")
        )
    )


def main():
    set_loglevel()
    logging.info(f"Running dungeon downloader version "
                 f"{version('dungeon-downloader')}")
    dungeondownloader.cli.main()
    logging.info("Run complete, exiting")


if __name__ == "__main__":
    main()
