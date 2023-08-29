import argparse as ap

import dungeondownloader.savewrapper


def main():
    """Run the CLI with Argparse and call the rest of the module afterward.
    """
    parser = ap.ArgumentParser(
        prog="Dungeon Downloader",
        description="A useful script for downloading, updating, and "
                    "verifying various dungeon related files."
    )
    parser.add_argument(
        "-r", "--root-domain",
        nargs=1,
        type=str,
        help="The root domain from which to download everything.",
        required=False
    )
    parser.add_argument(
        "-o", "--output-dir",
        nargs=1,
        type=str,
        help="The directory where to output everything. If there are "
             "files currently present in the directory, they will be "
             "checked for updates and only necessary files will be "
             "downloaded.",
        required=False
    )
    parser.add_argument(
        "-v", "--validate",
        action="store_true",
        help="Whether to recalculate the hashes of all files instead "
             "of using the cached hashes from the last run.",
    )
    parser.add_argument(
        "-d", "--delete-files",
        action="store_true",
        help="Whether to delete files that are not present in the "
             "patch list. Will ask for confirmation if the number of "
             "deleted files is high."
    )
    parser.set_defaults(func=dungeondownloader.savewrapper.main)
    args = parser.parse_args()
    args.func(**vars(args))
