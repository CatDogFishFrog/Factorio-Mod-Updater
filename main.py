import os
from multiprocessing.managers import Value
from site import abs_paths
from typing import List
import configparser
from mod_processor import parse_mod_files
from models.game_mod import GameMod
from web_api.factorio_web_api import FactorioAPIClient
from web_api.mod_downloader import ModDownloadManager
from web_api.mod_synchronizer import ModSynchronizer
from utils.singleton_console import ConsoleSingleton

# Console configuration
console = ConsoleSingleton(log_level="info")

# Default paths and settings
SETTINGS_FILE_PATH = "settings.ini"
DEFAULT_SETTINGS = {
    'Logging': {'level': 'INFO'},
    'Paths': {'mods': ''},
    'IgnoreList': {'ignore_list_file_path': 'ignore_mods.txt'}
}


def load_settings(file_path: str) -> configparser.ConfigParser:
    """
    Load settings from a .ini file. If the file does not exist, creates it with default settings.

    Returns:
        configparser.ConfigParser: Parsed configuration settings.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        with open(file_path, 'w') as configfile:
            config.read_dict(DEFAULT_SETTINGS)
            config.write(configfile)
        console.warning(f"Settings file created at {os.path.abspath(file_path)} with default values. Please verify.")
        wait_for_user_confirmation("If you want to modify the settings file, edit it and press 'N' to continue.")
    else:
        config.read(file_path)
    return config


def load_ignore_list(ignore_list_file_path: str) -> List[str]:
    """
    Loads mod names to ignore from the specified ignore list file.

    Returns:
        List[str]: List of mod names to ignore.
    """
    ignore_list = []
    if os.path.exists(ignore_list_file_path):
        with open(ignore_list_file_path, 'r') as file:
            ignore_list = [line.strip() for line in file]
        console.debug(f"Ignore list loaded with {len(ignore_list)} entries.")
    else:
        with open(ignore_list_file_path, 'w') as file:
            file.write("base\nquality")
        console.warning(f"Ignore list file created at {os.path.abspath(ignore_list_file_path)} with default entries.")
    return ignore_list


def find_installed_mods(mod_dir: str, ignore_list: List[str]) -> List[GameMod]:
    """
    Finds and returns a list of installed mods excluding those in the ignore list.
    """
    installed_mods = parse_mod_files.get_mods_list(mod_dir, ignore_list)
    console.info(f"Located {len(installed_mods)} installed mods in directory: {mod_dir}")
    return installed_mods


def start_download(mods: List[GameMod], ignore_list: List[str], downloader: ModDownloadManager) -> None:
    """
    Initiates the download of the latest releases for the specified mods, excluding those in the ignore list.
    """
    downloader.download_latest_releases(mods, ignore_list)
    console.info("All mods downloaded successfully.")


def wait_for_user_confirmation(prompt: str):
    """
    Pauses execution until the user presses 'N' to proceed, allowing for optional file adjustments.
    """
    console.info(prompt)
    while input().strip().lower() != 'n':
        pass #wait for user confirmation


def main():
    # Load settings and initialize components
    config = load_settings(SETTINGS_FILE_PATH)
    log_level = config.get("Logging", "level", fallback="INFO")
    console.set_log_level(log_level)

    mods_folder_path = config.get("Paths", "mods", fallback=DEFAULT_SETTINGS['Paths']['mods'])
    if not os.path.exists(mods_folder_path):
        console.error(f"Mods directory does not exist: {os.path.abspath(mods_folder_path)}")
        return
    ignore_list_file_path = config.get("IgnoreList", "ignore_list_file_path",
                                       fallback=DEFAULT_SETTINGS['IgnoreList']['ignore_list_file_path'])

    # Instantiate essential classes
    downloader = ModDownloadManager(download_dir=mods_folder_path)
    api_client = FactorioAPIClient()
    synchronizer = ModSynchronizer(api_client=api_client)

    # Load ignore list and installed mods
    ignore_list = load_ignore_list(ignore_list_file_path)

    try:
        installed_mods = find_installed_mods(mods_folder_path, ignore_list)
    except ValueError as err:
        console.error(f"Error loading installed mods: {err}")
        return

    # Check for available updates
    available_updates = synchronizer.find_updates_of_mods_list(installed_mods)
    if len(available_updates) == 0:
        console.info("No updates found.")
        return
    console.info(f"Found {len(available_updates)} mods with available updates.")

    # Allow user to modify the ignore list if necessary
    wait_for_user_confirmation("If you wish to update the ignore list, edit the file and press 'N' to continue.")
    ignore_list = load_ignore_list(ignore_list_file_path)
    # Start the download process
    start_download(available_updates, ignore_list, downloader)
    console.success("Process completed.")


if __name__ == '__main__':
    main()
