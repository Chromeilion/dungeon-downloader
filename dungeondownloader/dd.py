from __future__ import annotations

import logging
import os
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from typing import Optional, TypeVar

import requests
from tqdm import tqdm

from dungeondownloader.config_dict import hash_dict
from dungeondownloader.hashing import Hashing
from dungeondownloader.patch_file import file_list, PatchFile

_T = TypeVar("_T")


def confirm(question: str,
            default: Optional[bool] = None) -> bool:
    """Very simple yes/no prompt. Defaults to True.
    """
    if default is None:
        default = True

    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default:
        prompt = "[Y/n]"
    else:
        prompt = "[y/N]"

    while True:
        choice = input(" ".join([question, prompt])).lower()
        if choice == "":
            return default
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y'/'n').\n")


def download(url: str, filepath: str,
             pbar: tqdm[_T],
             chunk_size: Optional[int] = None) -> None:
    """
    Download some url and save it to a file. Takes a tqdm progress bar and
    updates it as the file downloads.

    Parameters
    ----------
    url : str
    filepath : str
    pbar : tqdm
    chunk_size : int
        default is 1024
    """
    if chunk_size is None:
        chunk_size = 1024

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    r = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for data in r.iter_content(chunk_size=chunk_size):
            size = f.write(data)
            pbar.update(size)


def download_patch(patch_file: PatchFile,
                   pbar: tqdm[_T]
                   ) -> None:
    """Simple wrapper around download that unpacks a patch file.
    """
    download(
        url=patch_file["full_url"],
        filepath=str(patch_file["full_path"]),
        pbar=pbar
    )


def read_patchlist(url: str) -> file_list:
    """
    Download and parse a text file where every line corresponds to a
    PatchFile type object.
    """
    r = requests.get(url)
    patch_file_list = r.content.split(b"\n")
    patch_file_list_parsed = [
        i.decode().replace("\\", "/").split(",") for i in patch_file_list
    ]
    patch_file_list_parsed = [i for i in patch_file_list_parsed if len(i) == 3]
    patch_files = []
    for i in patch_file_list_parsed:
        patch_file: PatchFile = {
            "path": Path(i[0][1:]),
            "url": i[0],
            "hash": i[1],
            "size": int(i[2])
        }
        patch_files.append(patch_file)
    return patch_files


def check_files(files: file_list,
                validate: bool,
                hashes: Optional[hash_dict] = None
                ) -> tuple[file_list, hash_dict]:
    """
    Compare hashes stored within the PatchFile objects with the provided
    hashes dictionary. If any of the hashes don't match, that file is
    marked as invalid and returned.

    If validate is passed, the hashes variable is completely
    recalculated for every file present in files.

    Parameters
    ----------
    files : file_list
    validate : bool
    hashes : Optional[hash_dict]

    Returns
    -------
    invalid : file_list
        Files whose hashes do not match
    hashes : hash_dict
        If validate is true, the new validated hashes. Any files present
        in files but not in hashes are added to hashes as well.
    """
    if hashes is None:
        hashes = {}

    invalid = []
    hasher = Hashing()
    for file in files:
        if not file["full_path"].exists():
            logging.debug(f"{file['full_path']} not found on disk")
            invalid.append(file)
        elif os.path.getsize(file["full_path"]) != file["size"]:
            logging.debug(f"{file['full_path']} has incorrect size")
            invalid.append(file)

    if validate:
        logging.info("Recalculating all local hashes")
        hashes = hasher.get_sha256_hash(
            files=[i["full_path"] for i in files if i not in invalid]
        )
    # If new PatchFiles are present, add them to the hash list.
    for i in files:
        if str(i["full_path"]) not in hashes:
            hashes[str(i["full_path"])] = i["hash"]

    # If the cached hash doesn't match the PatchFile hash, mark as invalid.
    for file in files:
        if hashes[str(file["full_path"])] != file["hash"]:
            invalid.append(file)

    return invalid, hashes


def calc_full_paths(root_dir: Path, files: file_list) -> None:
    for file in files:
        file["full_path"] = root_dir.joinpath(file["path"])


def calc_full_urls(url_root: str, files: file_list) -> None:
    for file in files:
        file["full_url"] = url_root + file["url"]


def update_files(files: file_list) -> None:
    """
    Download files from a list of PatchFile objects. The 'size'
    parameter is used to create a progress bar and estimate time
    remaining.
    Uses multiple threads to speed up the download (in some cases).
    """
    total = sum([i["size"] for i in files])
    pbar = tqdm(
        position=0,
        total=total,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading files",
        smoothing=0.15
    )
    with ThreadPool(4) as p:
        p.map(partial(download_patch, pbar=pbar), files)


def remove_redundant_files(hashes: dict[str, str],
                           patch_files: file_list) -> Optional[list[str]]:
    """
    Delete all files that exist in the hash dictionary but not in the
    patch list. Asks for confirmation if the number of files to delete is
    large.

    Returns
    -------
    deleted : Optional[list[str]]
        A list of all files that have been deleted in the form of full
        filepaths.
    """
    delete_list: list[str] = []
    all_filepaths = [str(i["full_path"]) for i in patch_files]
    for h in hashes:
        if h not in all_filepaths:
            delete_list.append(h)
    if delete_list:
        # In case the amount of files to delete is large, ask the user for
        # input.
        if len(delete_list) > 10:
            question = f"Found {len(delete_list)} files to delete when " \
                       f"updating, are you sure this is correct?"
            if not confirm(question=question, default=False):
                return None

        delete_path = [Path(i) for i in delete_list]
        existent = [i for i in delete_path if i.exists()]
        non_existent = [str(i) for i in delete_path if i not in existent]
        for file in existent:
            file.unlink()

        if non_existent:
            logging.error(f"Asked to delete the following files: \n"
                          f"{non_existent}\n"
                          f"But they do not exist. Continuing program "
                          f"execution anyway")
        no_deleted = len(delete_list) - (len(delete_list) - len(existent))
        logging.info(f"Deleted {no_deleted} files from disk that are no "
                     f"longer on the patch list")
        return delete_list
    else:
        return None


def check_maintenence(root_domain: str) -> bool:
    """Check whether the application is currently under maintenance.
    """
    r = requests.get(root_domain + "/MaintenanceLock.lck")
    if r.status_code == 200:
        return True
    return False


def update_invalid_files(invalid_patch_files: file_list,
                         patch_files: file_list,
                         patch_root: str) -> hash_dict:
    """Download updates to invalid files and check their hashes afterward.
    """
    hasher = Hashing()
    calc_full_urls(url_root=patch_root, files=patch_files)
    update_files(files=invalid_patch_files)
    new_hashes = hasher.get_sha256_hash(
        files=[i["full_path"] for i in invalid_patch_files]
    )
    for i in invalid_patch_files:
        if i["hash"] != new_hashes[str(i["full_path"])]:
            logging.error(f"The hash of the downloaded file "
                          f"{i['full_path']} does not match the hash "
                          f"provided online. Continuing program execution "
                          f"anyway")
    return new_hashes


def main(root_domain: str,
         output_dir: str,
         validate: bool,
         hashes: Optional[hash_dict] = None,
         remove_files: Optional[bool] = None
         ) -> tuple[Optional[hash_dict], Optional[hash_dict]]:
    """
    The main module workflow. Responsible for just about everything.

    Parameters
    ----------
    root_domain : str
    output_dir : str
    validate : bool
    hashes : Optional[hash_dict]
        Provided hashes are assumed to be from previous runs of the
        program and are assumed to be correct. If you think that these
        are wrong then set validate to True.
    remove_files : bool
        Whether to remove files that were previously downloaded, but are
        no longer present on the current patch list.

    Returns
    -------
    new_files, deleted_files : Optional[hash_dict]
        If any new files were downloaded, their paths and hashes are
        returned in new_files. If any files were deleted, their paths
        and hashes are returned in deleted_files.
    """
    if remove_files is None:
        remove_files = False

    new_files, deleted_files = None, None

    # Respect server maintenance. Downloading files before maintenance is
    # over could result in a corrupt installation or even a ban since you're
    # not supposed to be able to do it.
    if check_maintenence(root_domain=root_domain):
        logging.info("Servers are currently under maintenance, try again "
                     "later")
        return new_files, deleted_files

    output_dir_path = Path(output_dir)
    patch_root = root_domain + "/Patch"
    patch_file_list_location = "/PatchFileList.txt"

    patch_files = read_patchlist(root_domain + patch_file_list_location)
    calc_full_paths(output_dir_path, patch_files)

    invalid_patch_files, hashes = check_files(files=patch_files,
                                              hashes=hashes,
                                              validate=validate)

    if invalid_patch_files:
        new_files = update_invalid_files(
            patch_files=patch_files,
            invalid_patch_files=invalid_patch_files,
            patch_root=patch_root
        )

    if remove_files:
        deleted = remove_redundant_files(hashes=hashes,
                                         patch_files=patch_files)
        if deleted_files is not None:
            deleted_files = {i: hashes[i] for i in deleted}

    return new_files, deleted_files
