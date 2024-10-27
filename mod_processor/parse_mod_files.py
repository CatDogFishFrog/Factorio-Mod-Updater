import hashlib
import json
import os
import re
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.game_mod import GameMod, Release
from utils.singleton_console import ConsoleSingleton

console = ConsoleSingleton()

class ModProcessingError(Exception):
    """Custom exception for errors during processing individual mod files."""
    pass


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
            ModProcessingError: If there is an error reading the file.
        """
        sha1 = hashlib.sha1()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
        except IOError as error:
            raise ModProcessingError(f"Error reading file {file_path}: {error.strerror}")
        return sha1.hexdigest()


class ModFileRecognizer:
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

        ignored_mods_set = set(ignore_mods).union(ModFileRecognizer.STANDARD_MODS)
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
            ModProcessingError: If the directory does not exist.
        """
        pattern = re.compile(rf"{mod_name}_\d+\.\d+\.\d+\.zip")
        try:
            return [
                os.path.join(mods_dir_path, f)
                for f in os.listdir(mods_dir_path) if pattern.match(f)
            ]
        except FileNotFoundError:
            raise ModProcessingError(f"Directory {mods_dir_path} does not exist.")

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
            ModProcessingError: If there is an error in processing file hashes.
        """
        mod_zip_files = ModFileRecognizer.find_mod_files(mod.name, mods_dir_path)

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

        Raises:
            ValueError: If there is an error during concurrent processing of mod files.
        """
        try:
            with ThreadPoolExecutor() as executor:
                future_to_mod = {executor.submit(ModFileRecognizer.process_mod_file, mod, mods_dir_path): mod for mod in mods}

                for future in as_completed(future_to_mod):
                    mod = future_to_mod[future]
                    try:
                        future.result()  # Raise any exceptions occurred during processing
                    except ModProcessingError as e:
                        console.print_error(f"Error processing mod '{mod.name}': {e}")
                    except Exception as e:
                        console.print_error(f"Unexpected error with mod '{mod.name}': {e}")
        except Exception as e:
            raise ValueError("A critical error occurred during mod processing.") from e

        return mods


def get_mods_list(mods_dir_path: str, ignore_mods: Optional[List[str]] = None) -> List[GameMod]:
    """
    Retrieves the list of mods with additional file and SHA-1 hash information.

    Args:
        mods_dir_path (str): Path to the directory containing 'mod-list.json' and mod archives.
        ignore_mods (Optional[List[str]]): List of mods to ignore. Defaults to None.

    Returns:
        List[GameMod]: List of GameMod instances with file and hash data added.

    Raises:
        ValueError: If parsing the mod list fails or a critical error occurs.
    """
    try:
        console.print_info("Reading mod list from mod-list.json...")
        mods = ModFileRecognizer.parse_mod_list_json(mods_dir_path, ignore_mods)
        console.print_info("Processing mods to add file and hash data...")
        return ModFileRecognizer.process_mod_files(mods, mods_dir_path)
    except ValueError as e:
        console.print_error("Critical error while retrieving mods list.")
        raise e
