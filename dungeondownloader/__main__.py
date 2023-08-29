import logging
import os

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
    dungeondownloader.cli.main()


if __name__ == "__main__":
    main()
