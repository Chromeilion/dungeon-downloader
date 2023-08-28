import logging
import os
from pathlib import Path
from typing import TypedDict, Optional

import requests
from tqdm import tqdm

from dungeondownloader.hashing import Hashing


class PatchFileBase(TypedDict, total=True):
    """
    Required keys for the PatchFile dict.
    """
    path: Path
    hash: str
    size: int
    url: str


class PatchFile(PatchFileBase, total=False):
    """
    Optional keys for the PatchFile dict.
    """
    full_path: Path
    full_url: str


file_list = list[PatchFile]


def download(url: str, filepath: str, pbar: tqdm, chunk_size=1024):
    """
    Download a url and save it to a file. Takes a tqdm progress bar and
    updates it as the file downloads.

    Parameters
    ----------
    url : str
    filepath : str
    pbar : tqdm
    chunk_size : int
        default is 1024
    """
    r = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for data in r.iter_content(chunk_size=chunk_size):
            size = f.write(data)
            pbar.update(size)


def read_patchlist(url: str) -> file_list:
    """
    Parse a text file where every line is a file into a file_list.

    Parameters
    ----------
    url : str

    Returns
    -------
    file_list
    """
    r = requests.get(url)
    patch_file_list = r.content.split(b"\n")
    patch_file_list = [i.decode().replace("\\", "/").split(",") for i in
                       patch_file_list]
    patch_file_list = [i for i in patch_file_list if len(i) == 3]
    patch_files = []
    for i in patch_file_list:
        patch_files.append(
            {
                "path": Path(i[0][1:]),
                "url": i[0],
                "hash": i[1],
                "size": int(i[2])
            }
        )
    return patch_files


def check_files(files: file_list,
                validate: bool,
                hashes: Optional[dict[str, str]] = None
                ) -> tuple[list[Optional[PatchFile]], dict[str, str]]:
    """
    Compare hashes stored within the PatchFile objects with the provided
    hashes dictionary.
    If any of the hashes don't match, that file is marked as invalid and
    returned.

    If validate is passed, the hashes variable is completely
    recalculated for every file present in files.

    Parameters
    ----------
    files : file_list
    validate : bool
    hashes : Optional[dict[str, str]]

    Returns
    -------
    invalid : list[Optional[PatchFile]]
        Files whose hashes do not match
    hashes : dict[str, str]
        Either the exact same dictionary as initially provided, or if
        validate is true, the new validated hashes.
    """
    if hashes is None:
        hashes = {}
    invalid = []
    hasher = Hashing()
    for file in files:
        if not file["full_path"].exists():
            invalid.append(file)
        elif os.path.getsize(file["full_path"]) != file["size"]:
            invalid.append(file)

    if validate:
        hashes = hasher.get_sha256_hash(
            files=[i["full_path"] for i in files if i not in invalid]
        )
    else:
        for i in files:
            if str(i["full_path"]) not in hashes.keys():
                hashes[str(i["full_path"])] = i["hash"]

    for file in files:
        if hashes[str(file["full_path"])] != file["hash"]:
            invalid.append(file)

    return invalid, hashes


def calc_full_paths(root_dir: Path, files: file_list):
    for file in files:
        file["full_path"] = root_dir.joinpath(file["path"])


def calc_full_urls(url_root: str, files: file_list):
    for file in files:
        file["full_url"] = url_root + file["url"]


def update_files(files: file_list):
    """
    Download files from a list of PatchFile objects. The 'size'
    parameter is used to create a progress bar and estimate time
    remaining.

    Parameters
    ----------
    files : file_list
    """
    total = sum([i["size"] for i in files])
    pbar = tqdm(
        position=0,
        total=total,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading updates"
    )
    for file in files:
        os.makedirs(os.path.dirname(file["full_path"]), exist_ok=True)
        download(url=file["full_url"],
                 filepath=str(file["full_path"]),
                 pbar=pbar)


def main(root_domain: str,
         output_dir: str,
         validate: bool,
         hashes: Optional[dict[str, str]] = None) -> dict[str, str]:
    """
    The main module workflow. Responsible for getting the latest list
    of files, comparing the new list with what's currently on the disk,
    and downloading any new files that may have changed or are missing.

    Parameters
    ----------
    root_domain : str
    output_dir : str
    validate : bool
    hashes : Optional[dict[str, str]]
        Provided hashes are assumed to be from previous runs of the
        program and should be correct. If you think that these are
        wrong then set validate to True.

    Returns
    -------
    new_hashes : dict[str, str]
        If any new files were downloaded, their hashes are returned.
    """
    output_dir = Path(output_dir)
    patch_root = root_domain+"/Patch"
    patch_file_list_location = "/PatchFileList.txt"

    patch_files = read_patchlist(root_domain+patch_file_list_location)
    calc_full_paths(output_dir, patch_files)

    invalid_patch_files, hashes = check_files(files=patch_files,
                                              hashes=hashes,
                                              validate=validate)
    new_hashes = None
    if invalid_patch_files:
        hasher = Hashing()
        calc_full_urls(url_root=patch_root, files=patch_files)
        update_files(invalid_patch_files)
        new_hashes = hasher.get_sha256_hash(
            files=[i["full_path"] for i in invalid_patch_files]
        )
        for i in invalid_patch_files:
            if i["hash"] != new_hashes[str(i["full_path"])]:
                logging.error(f"The hash of the downloaded file "
                              f"{i['full_path']} does not match the hash "
                              f"provided online.")
    return new_hashes
