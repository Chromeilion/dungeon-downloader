from typing import TypedDict

from pydantic import TypeAdapter


class ConfigDictRequired(TypedDict, total=True):
    """Required config keys.
    """
    root_domain: str
    output_dir: str


# This is useful as an import in other parts of the code
hash_dict = dict[str, str]


class ConfigDictOptional(ConfigDictRequired, total=False):
    """Optional config keys.
    """
    hashes: hash_dict


class ConfigDict:
    """
    Attributes
    ----------
    cd : ConfigDictOptional
        Regular typed dict that specifies the config json data type.
    cdp : TypeAdapter
        The cd type adapted through Pydantic for use with type checking.

    Notes
    -----
    The cdp attribute is the reason this entire module needs Python 3.12.
    It's possible to use the TypeAdapter in Python < 3.12, but the
    workaround requires adding a dependency which I don't want to do.
    """
    cd = ConfigDictOptional
    cdp = TypeAdapter(cd)
