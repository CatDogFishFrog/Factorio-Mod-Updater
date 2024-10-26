import hashlib
import json
import os
import re
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from game_mod import GameMod, Release


class FileHasher:
    @staticmethod
    def calculate_sha1(file_path: str) -> str:
        """
        Calculates the SHA-1 hash of the specified file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: The SHA-1 hash of the file content.

        Raises:
            ValueError: If there is an error reading the file.
        """
        sha1 = hashlib.sha1()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)  # Read in 64k chunks
                    if not data:
                        break
                    sha1.update(data)
        except IOError as error:
            raise ValueError(f"Error reading file {file_path}: {error.strerror}")
        return sha1.hexdigest()


class ModFileManager:
    STANDARD_MODS = {"base", "elevated-rails", "quality", "space-age"}

    @staticmethod
    def parse_mod_list_json(mods_dir_path: str, ignore_mods: Optional[List[str]] = None) -> List[GameMod]:
        """
        Reads and parses the 'mod-list.json' file, excluding ignored mods, and returns a list of GameMod instances.

        Args:
            mods_dir_path (str): Path to the directory containing 'mod-list.json'.
            ignore_mods (Optional[List[str]]): List of mods to ignore. Defaults to None.

        Returns:
            List[GameMod]: A list of GameMod instances without ignored mods.

        Raises:
            ValueError: If 'mod-list.json' does not exist or is improperly formatted.
        """
        if ignore_mods is None:
            ignore_mods = []

        mod_list_path = os.path.join(mods_dir_path, "mod-list.json")
        if not os.path.isfile(mod_list_path):
            raise ValueError(f"File mod-list.json does not exist in {mods_dir_path}.")

        with open(mod_list_path, "r", encoding="utf-8") as f:
            mod_list_data = json.load(f)

        ignored_mods_set = set(ignore_mods).union(ModFileManager.STANDARD_MODS)
        mods = [
            GameMod(name=mod["name"])
            for mod in mod_list_data.get("mods", [])
            if mod["name"] not in ignored_mods_set
        ]

        return mods

    @staticmethod
    def find_mod_files(mod_name: str, mods_dir_path: str) -> List[str]:
        """
        Finds all files in the mods directory that match the pattern '{mod_name}_<version>.zip'.

        Args:
            mod_name (str): Name of the mod to search for.
            mods_dir_path (str): Path to the directory containing mod files.

        Returns:
            List[str]: List of file paths matching the mod name pattern.

        Raises:
            ValueError: If the directory does not exist.
        """
        pattern = re.compile(rf"{mod_name}_\d+\.\d+\.\d+\.zip")
        try:
            return [
                os.path.join(mods_dir_path, f)
                for f in os.listdir(mods_dir_path) if pattern.match(f)
            ]
        except FileNotFoundError:
            raise ValueError(f"Directory {mods_dir_path} does not exist.")

    @staticmethod
    def process_mod_file(mod: GameMod, mods_dir_path: str) -> GameMod:
        """
        Processes a GameMod instance to locate its files, extract version info, and calculate SHA-1 hashes.

        Args:
            mod (GameMod): An instance of GameMod to process.
            mods_dir_path (str): Path to the directory containing mod files.

        Returns:
            GameMod: Updated GameMod instance with associated file data and SHA-1 hashes.

        Raises:
            ValueError: If there is an error in processing file hashes.
        """
        mod_zip_files = ModFileManager.find_mod_files(mod.name, mods_dir_path)

        for mod_file_path in mod_zip_files:
            mod_file_name = os.path.basename(mod_file_path)
            mod_version = re.search(rf"{mod.name}_(\d+\.\d+\.\d+)\.zip", mod_file_name).group(1)
            mod_sha1 = FileHasher.calculate_sha1(mod_file_path)
            release = Release(
                file_name=mod_file_name,
                sha1=mod_sha1,
                version=mod_version
            )
            mod.add_release(release)

        return mod

    @staticmethod
    def process_mod_files(mods: List[GameMod], mods_dir_path: str) -> List[GameMod]:
        """
        Processes multiple GameMod instances using multithreading, finding and hashing their associated files.

        Args:
            mods (List[GameMod]): List of GameMod instances to process.
            mods_dir_path (str): Path to the directory containing mod files.

        Returns:
            List[GameMod]: Updated list of GameMod instances with additional file information.
        """
        try:
            with ThreadPoolExecutor() as executor:
                future_to_mod = {executor.submit(ModFileManager.process_mod_file, mod, mods_dir_path): mod for mod in mods}

                for future in as_completed(future_to_mod):
                    mod = future_to_mod[future]
                    try:
                        future.result()  # Raise any exceptions occurred during processing
                    except Exception as e:
                        print(f"An error occurred while processing mod '{mod.name}': {e}")

        except Exception as e:
            raise ValueError(f"An error occurred while processing mod files: {e}")

        return mods


def get_mods_list(mods_dir_path: str, ignore_mods: Optional[List[str]] = None) -> List[GameMod]:
    """
    Retrieves the list of mods with additional file and SHA-1 hash information.

    Args:
        mods_dir_path (str): Path to the directory containing 'mod-list.json' and mod archives.
        ignore_mods (Optional[List[str]]): List of mods to ignore. Defaults to None.

    Returns:
        List[GameMod]: List of GameMod instances with file and hash data added.
    """
    mods = ModFileManager.parse_mod_list_json(mods_dir_path, ignore_mods)
    return ModFileManager.process_mod_files(mods, mods_dir_path)
