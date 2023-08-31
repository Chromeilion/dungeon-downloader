from __future__ import annotations

import logging
import os
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from typing import Optional, TypeVar

import requests
from tqdm import tqdm

from dungeondownloader.hashing import Hashing, HashDict
from dungeondownloader.patch_file import PatchFileList, PatchFile

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


def download(url: str,
             filepath: str,
             pbar: tqdm[_T],
             chunk_size: Optional[int] = None) -> None:
    """
    Download from the provided url and save it to a file.

    Parameters
    ----------
    url : url to download the file from
    filepath : path where to save file
    pbar : tqdm progress bar that will be updated with each iteration
    chunk_size : amount do download and save at once, default is 1024
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


def read_patchlist(url: str) -> PatchFileList:
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


def check_files(files: PatchFileList,
                validate: bool,
                hashes: Optional[HashDict] = None
                ) -> tuple[PatchFileList, HashDict]:
    """
    Compare hashes stored within the PatchFile objects with the provided
    hashes dictionary. If any of the hashes don't match, that file is
    marked as invalid and returned.

    If validate is passed, the hashes variable is completely
    recalculated for every file present in files.

    Parameters
    ----------
    files : list of files to check
    validate : whether to recalculate all local hashes
    hashes : hashes from the last run, assumed to be correct unless
        validate is True

    Returns
    -------
    invalid : Files detected as invalid
    hashes : If validate is true, the new validated hashes. Any files
        present in files but not in hashes are added to hashes as well
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


def calc_full_paths(root_dir: Path, files: PatchFileList) -> None:
    for file in files:
        file["full_path"] = root_dir.joinpath(file["path"])


def calc_full_urls(url_root: str, files: PatchFileList) -> None:
    for file in files:
        file["full_url"] = url_root + file["url"]


def update_files(files: PatchFileList) -> None:
    """
    Download files from a list of PatchFile objects.
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


def remove_redundant_files(hashes: HashDict,
                           patch_files: PatchFileList) -> Optional[list[str]]:
    """
    Delete all files that exist in the hash dictionary but not in the
    patch list. Asks for confirmation if the number of files to delete is
    large.

    Returns
    -------
    deleted : A list of all files that have been deleted in the form of
        full filepaths.
    """
    patch_files_str = [str(i["full_path"]) for i in patch_files]
    delete_list = [h for h in hashes if h not in patch_files_str]

    if delete_list:
        # In case the amount of files to delete is large, ask the user for
        # input.
        if len(delete_list) > 10:
            question = f"Found {len(delete_list)} files to delete when " \
                       f"updating, are you sure this is correct?"
            if not confirm(question=question, default=False):
                return None

        for file in delete_list:
            try:
                Path(file).unlink()
            except FileNotFoundError:
                logging.error(f"Asked to delete the following file: "
                              f"{file}, but it does not exist. Continuing "
                              f"program execution anyway")

        logging.info(f"Removed {len(delete_list)} files that are no longer "
                     f"on the patch list")
        return delete_list
    return None


def check_maintenence(root_domain: str) -> bool:
    """Check whether the application is currently under maintenance.
    """
    r = requests.get(root_domain + "/MaintenanceLock.lck")
    if r.status_code == 200:
        return True
    return False


def update_invalid_files(invalid_patch_files: PatchFileList,
                         patch_files: PatchFileList,
                         patch_root: str) -> HashDict:
    """Download updates for invalid files and check their hashes afterward.
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
         hashes: Optional[HashDict] = None,
         remove_files: Optional[bool] = None
         ) -> tuple[Optional[HashDict], Optional[HashDict]]:
    """
    The main module workflow. Responsible for just about everything.

    Parameters
    ----------
    root_domain : the base domain from which to calculate all other urls
    output_dir : where to save all downloaded files
    validate : whether to check integrity of all files
    hashes : hashes from previous runs, assumed to be correct
    remove_files : whether to remove files that are present in hashes
        but not on the current patch list

    Returns
    -------
    new_files, deleted_files : If any new files were downloaded or if
        any files were deleted, their paths and hashes are returned
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
