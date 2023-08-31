from typing import TypedDict

from dungeondownloader.hashing import HashDict


class ConfigDictRequired(TypedDict, total=True):
    """Required config keys.
    """
    root_domain: str
    output_dir: str


class ConfigDict(ConfigDictRequired, total=False):
    """Optional config keys.
    """
    hashes: HashDict
