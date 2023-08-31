import hashlib
import logging
import os
import platform
from functools import partial
from multiprocessing.dummy import Pool
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Union

from tqdm import tqdm

# This is useful as an import in other parts of the code
HashDict = dict[str, str]


class Hashing:
    """Class containing functions for calculating hashes.
    """
    def get_sha256_hash(self,
                        files: Union[list[Path], Path]) -> HashDict:
        """
        Get the sha256 hash of a file. Attempts to use platform
        specific utilities but falls back to pure Python if there is an
        error.

        Uses multithreading and number of processes equal to number of
        CPU cores.

        Parameters
        ----------
        files : Either a single Path object or a list of Path objects

        Returns
        -------
        hash_dict : dictionary where the key is the provided file path and
            the value is the hash
        """
        if not isinstance(files, list):
            files = [files]

        system = platform.system()
        logging.debug(f"Identified {system} as platform when calculating "
                      f"hashes")
        try:
            if system in ["Darwin", "Linux"]:
                sh256_hash = self._sha256sum(files=files)

            else:
                sh256_hash = self._get_sha256_hash_generic(files=files)

        except ChildProcessError:
            sh256_hash = self._get_sha256_hash_generic(files=files)

        return sh256_hash

    @staticmethod
    def _get_sha256_hash_generic(files: list[Path]) -> HashDict:
        """
        Native Python sha256 hash calculation implementation, should
        work anywhere where Python works but is slow.
        """
        hashes = {}
        for i in files:
            full_hash = hashlib.sha256()
            with open(str(i), 'rb') as f:
                while chunk := f.read(8192):
                    full_hash.update(chunk)
            hashes[str(i)] = full_hash.hexdigest()

        return hashes

    @staticmethod
    def _sha256sum(files: list[Path]) -> HashDict:
        """
        Use the sha256sum command with multiple threads to quickly
        calculate file hashes.
        """
        commands = [("sha256sum", str(i)) for i in files]
        popen_wrap = partial(Popen, stdout=PIPE, stderr=PIPE)
        results = {}
        with Pool(os.cpu_count()) as pool:
            for result in tqdm(pool.imap(popen_wrap, commands),
                               desc="Calculating file hashes",
                               total=len(commands)):
                err = result.stderr.readlines()
                if err:
                    raise ChildProcessError("Running sha256sum returned a "
                                            "non-zero exit code")
                output = str(result.stdout.readlines()).split(" ", 1)
                results[output[1][1:-4]] = output[0][3:]
        return results
