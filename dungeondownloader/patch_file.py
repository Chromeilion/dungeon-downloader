from pathlib import Path
from typing import TypedDict


class PatchFileBase(TypedDict, total=True):
    """Required keys for the PatchFile dict.
    """
    path: Path
    hash: str
    size: int
    url: str


class PatchFile(PatchFileBase, total=False):
    """Optional keys for the PatchFile dict.
    """
    full_path: Path
    full_url: str


# Useful when working with a lot of patch files
PatchFileList = list[PatchFile]
