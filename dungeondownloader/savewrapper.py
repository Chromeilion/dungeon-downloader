import json
import logging
from pathlib import Path
from typing import Optional, TypedDict

from pydantic import TypeAdapter, ValidationError
import appdirs

import dungeondownloader.dd
import importlib.metadata


class ConfigDictBase(TypedDict, total=True):
    root_domain: str
    output_dir: str


class ConfigDict(ConfigDictBase, total=False):
    hashes: dict[str, str]


cd = TypeAdapter(ConfigDict)


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
        return Path("./config.json")
    return Path(appdirs.user_data_dir(appname="dungeon-downloader",
                                      appauthor="Chromeilion"))


def generate_config(root_domain: Optional[str] = None,
                    output_dir: Optional[str] = None,
                    hashes: Optional[dict[str, str]] = None):
    if root_domain is None:
        root_domain = input("Please specify the root domain to use:")
    if output_dir is None:
        output_dir = input("Please specify the output directory:")
    config: ConfigDict = {
        "root_domain": root_domain,
        "output_dir": output_dir,
    }
    if hashes is not None:
        config["hashes"] = hashes

    with open(load_config_filepath(), "w") as f:
        json.dump(config, f)
    return config


def read_and_validate_config(root_domain: Optional[str] = None,
                             output_dir: Optional[str] = None) -> ConfigDict:
    config: ConfigDict
    with open(load_config_filepath(), "r") as f:
        config = json.load(f)

    try:
        cd.validate_python(config)
    except ValidationError:
        logging.warning("The current config is invalid, generating a "
                        "new one")
        config = generate_config(root_domain=root_domain,
                                 output_dir=output_dir)

    if config["root_domain"] != root_domain and root_domain is not None:
        logging.info("New value for root-domain passed, overwriting "
                     "old value present in config")
        config = generate_config(root_domain=root_domain,
                                 output_dir=config["output_dir"])
    if config["output_dir"] != output_dir and output_dir is not None:
        logging.info("New value for output-dir passed, overwriting old "
                     "value present in config")
        config = generate_config(root_domain=config["root_domain"],
                                 output_dir=output_dir)
    return config


def update_hashes(config: ConfigDict,
                  hashes: Optional[dict[str, str]] = None):
    logging.debug("Saving hashes")
    if hashes is None:
        logging.info("No new hashes found")
        return
    if "hashes" not in config.keys():
        config["hashes"] = {}

    for key, value in hashes.items():
        if key not in config["hashes"].keys():
            logging.debug(f"New hash found for {key}")
            config["hashes"][key] = value
        elif config["hashes"][key] != value:
            logging.debug(f"Hash changed for {key}")
            config["hashes"][key] = value

    generate_config(root_domain=config["root_domain"],
                    output_dir=config["output_dir"],
                    hashes=hashes)


def main(validate: bool,
         root_domain: Optional[list[str]] = None,
         output_dir: Optional[list[str]] = None,
         *_, **__):
    if root_domain is not None:
        root_domain = root_domain[0]
    if output_dir is not None:
        output_dir = output_dir[0]
    config: ConfigDict

    logging.info(f"Running dungeon downloader version "
                 f"{importlib.metadata.version('dungeon-downloader')}")

    if not load_config_filepath().exists():
        logging.info("No config file detected, generating new file")
        config = generate_config(root_domain=root_domain,
                                 output_dir=output_dir)
    else:
        logging.info("Config file detected, loading file")
        config = read_and_validate_config(root_domain=root_domain,
                                          output_dir=output_dir)

    hashes = None
    if "hashes" in config.keys():
        hashes = config["hashes"]
    new_hashes = dungeondownloader.dd.main(root_domain=config["root_domain"],
                                           output_dir=config["output_dir"],
                                           hashes=hashes,
                                           validate=validate)
    update_hashes(config=config, hashes=new_hashes)
