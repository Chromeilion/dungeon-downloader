import json
import logging
from pathlib import Path
from typing import Optional

import appdirs
from pydantic import ValidationError

import dungeondownloader.dd
from dungeondownloader.config_dict import ConfigDict


def load_config_filepath() -> Path:
    """
    Load the path to the config file. First looks in the working
    directory and then at standard system directories.

    If no config file is present, it will return the location where it
    should be according to the system standard.

    Returns
    -------
    config_path : Path
    """
    if Path("./config.json").exists():
        config_path = Path("./config.json")
    else:
        config_path = Path(
            appdirs.user_data_dir(
                appname="dungeon-downloader",
                appauthor="Chromeilion"
            )
        ).joinpath("config.json")
    if config_path.exists():
        logging.info(f"Found config at {config_path}")
    else:
        logging.info(f"Config file not found, setting location to "
                     f"{config_path}")
    return config_path


def generate_config(config_location: Path,
                    root_domain: Optional[str] = None,
                    output_dir: Optional[str] = None,
                    hashes: Optional[dict[str, str]] = None):
    """
    Create a new config and write it to disk.

    Parameters
    ----------
    config_location : Path
    root_domain : Optional[str]
    output_dir : Optional[str]
    hashes : Optional[dict[str, str]]
    """
    if root_domain is None:
        root_domain = input("Please specify the root domain to use:")
    if output_dir is None:
        output_dir = input("Please specify the output directory:")
    config: ConfigDict.cd = {
        "root_domain": root_domain,
        "output_dir": output_dir,
    }
    if hashes is not None:
        config["hashes"] = hashes

    config_location.parent.mkdir(exist_ok=True)
    with open(config_location, "w") as f:
        json.dump(config, f)
    logging.info(f"Saved config file to {config_location}")
    return config


def read_and_validate_config(config_location: Path,
                             root_domain: Optional[str] = None,
                             output_dir: Optional[str] = None
                             ) -> ConfigDict.cd:
    """
    Load a config file and use Pydantic to validate it against the
    ConfigDict type.
    If a ValidationError is encountered, a new config with correct type
    is generated.

    This module is important for whenever there is a change to the
    ConfigDict type between updates for example.
    The current way of handling it (regenerating the whole file) is not
    ideal, perhaps it would be better to try and salvage what parts of
    the file are recognizable and build the new file from that.
    """
    config: ConfigDict.cd
    with open(config_location, "r") as f:
        config = json.load(f)
    logging.debug(f"Loaded config file, attempting to validate")
    try:
        ConfigDict.cdp.validate_python(config)
        logging.info("Config successfully loaded and validated")
    except ValidationError:
        logging.warning("The current config is invalid, generating a "
                        "new one")
        config = generate_config(root_domain=root_domain,
                                 output_dir=output_dir,
                                 config_location=config_location)

    if config["root_domain"] != root_domain and root_domain is not None:
        logging.info("New value for root-domain passed, overwriting "
                     "old value present in config")
        config = generate_config(root_domain=root_domain,
                                 output_dir=config["output_dir"],
                                 config_location=config_location)
    if config["output_dir"] != output_dir and output_dir is not None:
        logging.info("New value for output-dir passed, overwriting old "
                     "value present in config")
        config = generate_config(root_domain=config["root_domain"],
                                 output_dir=output_dir,
                                 config_location=config_location)
    return config


def add_new_hashes(new_hashes: dict[str, str], hash_dict: dict[str, str]):
    """
    Add/update hashes in hash_dict based on values in new_hashes.
    Performs operations on hash_dict in-place.
    """
    for key, value in new_hashes.items():
        if key not in hash_dict:
            logging.debug(f"Local hash doesn't exist for {key}, creating new "
                          f"entry and saving hash to local database")
            hash_dict[key] = value
        elif hash_dict[key] != value:
            logging.debug(f"Hash changed for {key}, saving new hash to local "
                          f"database")
            hash_dict[key] = value
        else:
            logging.debug(f"Asked to update {key} in the local hash database, "
                          f"but there's nothing to update. This is normal if "
                          f"the file is new.")


def remove_hashes(deleted_hashes: dict[str, str], hash_dict: dict[str, str]):
    """
    Remove hashes from a hash_dict in-place based on hashes in
    deleted_hashes.
    """
    for key, value in deleted_hashes.items():
        if key in hash_dict:
            logging.debug(f"Removing {key} from local hash cache")
            hash_dict.pop(key)
        else:
            logging.error(f"Asked to remove {key} from local hash cache, but "
                          f"it is not present in the cache")


def update_hashes(config_location: Path,
                  config: ConfigDict.cd,
                  new_hashes: Optional[dict[str, str]] = None,
                  deleted_hashes: Optional[dict[str, str]] = None):
    """
    Given a config dict, a dict of new hashes, and a dict
    of hashes to remove, update config with the new hashes, remove the
    hashes in the removal list, and save the new updated file.

    Parameters
    ----------
    config : ConfigDict.cd
    new_hashes : Optional[dict[str, str]]
    deleted_hashes : Optional[dict[str, str]]
    config_location : Path

    Notes
    -----
    This function is longer (and slower) than it needs to be because
    every case is getting logged. While it certainly adds to the code
    complexity, logging also makes it much easier to debug issues, so I
    think its worth it.
    """
    logging.debug("Updating hashes")
    if "hashes" not in config:
        logging.debug("Hashes not found in config, creating new hashes "
                      "entry")
        config["hashes"] = {}
    hash_dict = config["hashes"]
    if new_hashes is None:
        logging.debug("No new hashes found")
    else:
        add_new_hashes(new_hashes=new_hashes, hash_dict=hash_dict)
    if deleted_hashes is None:
        logging.debug("No hashes deleted")
    else:
        remove_hashes(deleted_hashes=deleted_hashes, hash_dict=hash_dict)
    if new_hashes is not None or deleted_hashes is not None:
        generate_config(root_domain=config["root_domain"],
                        output_dir=config["output_dir"],
                        hashes=hash_dict,
                        config_location=config_location)


def main(validate: bool,
         delete_files: bool,
         root_domain: Optional[list[str]] = None,
         output_dir: Optional[list[str]] = None,
         *_, **__):
    """
    Function responsible for loading and saving data to/from the config
    file.

    Parameters
    ----------
    delete_files : bool
        Whether to delete files not present in the patch list
    validate : bool
        Whether to recalculate and check hashes of all files
    root_domain
        The root domain from which to calculate download paths
    output_dir
        Where to save all the files
    """
    if root_domain is not None:
        root_domain = root_domain[0]
    if output_dir is not None:
        output_dir = output_dir[0]
    config: ConfigDict.cd

    config_filepath = load_config_filepath()
    if not config_filepath.exists():
        logging.info("Generating new config file")
        config = generate_config(root_domain=root_domain,
                                 output_dir=output_dir,
                                 config_location=config_filepath)
    else:
        logging.info("Loading existing config file")
        config = read_and_validate_config(root_domain=root_domain,
                                          output_dir=output_dir,
                                          config_location=config_filepath)

    hashes = None
    if "hashes" in config.keys():
        hashes = config["hashes"]
    logging.info(f"Running with root domain: {config['root_domain']} and "
                 f"output directory: {config['output_dir']}")
    new_hashes, deleted_hashes = dungeondownloader.dd.main(
        root_domain=config["root_domain"],
        output_dir=config["output_dir"],
        hashes=hashes,
        validate=validate,
        remove_files=delete_files
    )
    update_hashes(config=config,
                  new_hashes=new_hashes,
                  deleted_hashes=deleted_hashes,
                  config_location=config_filepath)
