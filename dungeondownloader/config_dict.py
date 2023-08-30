from typing import TypedDict

from pydantic import TypeAdapter


class ConfigDictRequired(TypedDict, total=True):
    """Required config keys.
    """
    root_domain: str
    output_dir: str


# This is useful as an import in other parts of the code
hash_dict = dict[str, str]


class ConfigDict(ConfigDictRequired, total=False):
    """Optional config keys.
    """
    hashes: hash_dict


ConfigDictPydantic = TypeAdapter(ConfigDict)
