import hashlib
import json
import os
import re
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def _parse_mod_list_json(mods_dir_path: str, ignor_mods: Optional[List[str]] = None) -> Dict:
    """
    Process the mod-list.json within the mod_path.

    Args:
        mods_dir_path (str): Path to the directory containing mod-list.json.
        ignor_mods (List[str], optional): List of mods to ignore.

    Returns:
        Dict: Parsed mod list.

    Raises:
        ValueError: If the directory or file does not exist.
    """
    if ignor_mods is None:
        ignor_mods = []

    if not os.path.exists(mods_dir_path):
        raise ValueError(f"Directory {mods_dir_path} does not exist.")
    mod_list_path = os.path.join(mods_dir_path, "mod-list.json")
    if not os.path.isfile(mod_list_path):
        raise ValueError(f"File mod-list.json does not exist in {mods_dir_path}.")

    with open(mod_list_path, "r", encoding="utf-8") as f:
        mod_list = json.load(f)

    # Add standard Factorio modules to ignor_mods
    standard_mods = {"base", "elevated-rails", "quality", "space-age"}
    ignor_mods_set = set(ignor_mods).union(standard_mods)

    # Clean mod_list["mods"]
    mod_list["mods"] = [mod for mod in mod_list.get("mods", []) if mod["name"] not in ignor_mods_set]

    return mod_list


def _calculate_sha1(file_path: str) -> str:
    """Calculate SHA-1 hash of a file."""
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


def _find_mod_files(mod_name: str, mods_dir_path: str) -> List[str]:
    """
    Find all files in the mods directory that match the pattern {mod_name}_*.zip

    Args:
        mod_name (str): The name of the mod to search for.
        mods_dir_path (str): Path to the directory containing mod archives.

    Returns:
        List[str]: List of matching file paths.

    Raises:
        ValueError: If the directory does not exist.
    """
    pattern = re.compile(rf"{re.escape(mod_name)}_\d+\.\d+\.\d+\.zip")
    try:
        mod_files = [f for f in os.listdir(mods_dir_path) if pattern.match(f)]
    except FileNotFoundError:
        raise ValueError(f"Directory {mods_dir_path} does not exist.")

    return [os.path.join(mods_dir_path, f) for f in mod_files]


def _process_mod_file(mod: Dict, mods_dir_path: str) -> Dict:
    """
    Process a single mod, find its files, and calculate SHA-1 hashes.

    Args:
        mod (Dict): Mod information.
        mods_dir_path (str): Path to the directory containing mod archives.

    Returns:
        Dict: Updated mod with additional fields (file_name, version, sha1).
    """
    mod_name = mod["name"]
    mod_zip_files = _find_mod_files(mod_name, mods_dir_path)

    for mod_file_path in mod_zip_files:
        mod_file_name = os.path.basename(mod_file_path)
        mod_version = re.search(rf"{re.escape(mod_name)}_(\d+\.\d+\.\d+)\.zip", mod_file_name).group(1)
        mod_sha1 = _calculate_sha1(mod_file_path)

        mod.update({
            "file_name": mod_file_name,
            "version": mod_version,
            "sha1": mod_sha1
        })

    return mod


def _process_mod_files(mod_list: Dict, mods_dir_path: str) -> Dict:
    """
    Find mod archives and calculate their SHA-1 hash using multithreading.

    Args:
        mod_list (Dict): Parsed mod list.
        mods_dir_path (str): Path to the directory containing mod archives.

    Returns:
        Dict: Updated mod_list with additional fields for each mod.
    """
    try:
        with ThreadPoolExecutor() as executor:
            future_to_mod = {executor.submit(_process_mod_file, mod, mods_dir_path): mod for mod in mod_list["mods"]}

            for future in as_completed(future_to_mod):
                mod = future_to_mod[future]
                try:
                    future.result()  # Raises any exception if occurred
                except Exception as e:
                    print(f"An error occurred while processing mod '{mod['name']}': {e}")

    except Exception as e:
        raise ValueError(f"An error occurred while processing mod files: {e}")

    return mod_list


def get_mods_list(mods_dir_path: str, ignor_mods: Optional[List[str]] = None) -> Dict:
    """
    Get the list of mods with additional file information and SHA-1 hash.

    Args:
        mods_dir_path (str): Path to the directory containing mod-list.json and mod archives.
        ignor_mods (List[str], optional): List of mods to ignore.

    Returns:
        Dict: Updated mod_list with additional fields for each mod.
    """
    mod_list = _parse_mod_list_json(mods_dir_path, ignor_mods)
    return _process_mod_files(mod_list, mods_dir_path)