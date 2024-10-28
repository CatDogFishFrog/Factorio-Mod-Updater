import os
import random
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from exceptions.exceptions import DownloadError, EmptyFileError
from models.game_mod import GameMod, Release
from utils.file_hasher import FileHasher
from utils.singleton_console import ConsoleSingleton

# Console setup
console = ConsoleSingleton()

class ModValidator:
    """
    Utility class to validate mod download parameters.
    """

    @staticmethod
    def validate(name: str, version: str, download_dir: str):
        """
        Validate the inputs for mod download, checking for non-empty mod name,
        version, and a valid download directory.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if not name or not version:
            raise ValueError("Mod name and version must be provided.")
        if not os.path.isdir(download_dir):
            raise ValueError(f"Invalid path: {download_dir}")

class ModDownloader:
    """
    Handles the downloading of individual mods with retry and validation mechanisms.
    """

    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    @staticmethod
    def get_file_size_in_mb(download_link: str) -> Optional[float]:
        """
        Fetches file size from the download link header without downloading the content.

        Args:
            download_link (str): The URL of the file.

        Returns:
            Optional[float]: File size in MB if available; None if not.
        """
        try:
            head_response = requests.head(download_link, timeout=10)
            head_response.raise_for_status()
            file_size = int(head_response.headers.get('Content-Length', 0))
            return file_size / (1024 * 1024) if file_size > 0 else None
        except Exception as e:
            console.warning(f"Could not retrieve file size: {e}")
            return None

    def download_mod(self, name: str, version: str) -> str:
        """
        Initiates download of a specified mod version, with retry on failure.

        Args:
            name (str): The name of the mod to download.
            version (str): The version of the mod to download.

        Returns:
            str: The file path of the downloaded mod.

        Raises:
            DownloadError: If download fails after retries.
        """
        ModValidator.validate(name, version, self.download_dir)
        download_link = self._generate_download_link(name, version)
        file_path = os.path.join(self.download_dir, f"{name}_{version}.zip")

        # Retrieve and log the file size if available
        file_size_mb = self.get_file_size_in_mb(download_link)
        if file_size_mb:
            console.info(f"Starting download for {name} v{version} (Size: {file_size_mb:.2f} MB)")
        else:
            console.info(f"Starting download for {name} v{version} (Size: unknown)")

        try:
            return self._download_with_retry(download_link, file_path)
        except DownloadError as e:
            console.error(f"Download failed for {name} v{version}: {e}")
            raise

    def _generate_download_link(self, name: str, version: str) -> str:
        """
        Generates a download link with an anti-cache parameter to ensure fresh retrieval.

        Returns:
            str: The constructed download URL for the mod.
        """
        anticache = random.randint(1, 1_000_000_000)
        return f"https://mods-storage.re146.dev/{name}/{version}.zip?anticache={anticache}"

    def _download_with_retry(self, download_link: str, file_path: str) -> str:
        """
        Downloads a mod with a retry mechanism on network errors.

        Returns:
            str: The file path of the downloaded mod.

        Raises:
            DownloadError: If both attempts fail.
        """
        try:
            return self._download_from_url(download_link, file_path)
        except DownloadError as e:
            console.warning(f"Retrying download for {file_path} due to network error: {e}")
            return self._download_from_url(download_link, file_path)

    def _download_from_url(self, download_link: str, file_path: str) -> str:
        """
        Performs the actual download and verifies the downloaded file's integrity.

        Returns:
            str: The file path of the downloaded mod.

        Raises:
            DownloadError: If a network issue occurs or if the file is empty.
        """
        try:
            response = requests.get(download_link, stream=True, timeout=10)
            response.raise_for_status()
            self._save_file(response, file_path)

            if os.path.getsize(file_path) == 0:
                raise EmptyFileError("Downloaded file is empty.")
            console.debug(f"Downloaded file saved successfully at {file_path}")
            return file_path
        except (HTTPError, ConnectionError, Timeout) as e:
            raise DownloadError(f"Network error during download: {e}")

    def _save_file(self, response, file_path: str):
        """
        Saves the downloaded content in chunks to the specified file path.
        """
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        console.debug(f"File saved at {file_path} with size {os.path.getsize(file_path)} bytes")

class ModDownloadManager:
    """
    Manages the download process for multiple mods concurrently, with logging and error handling.
    """

    def __init__(self, download_dir: str = "temp"):
        self.download_dir = download_dir
        self.downloader = ModDownloader(download_dir)

    def download_latest_release(self, game_mod: GameMod):
        """
        Downloads the latest release of a specific mod and verifies its integrity.

        Args:
            game_mod (GameMod): The mod to download.

        Returns:
            str: The file path of the downloaded mod.

        Raises:
            DownloadError: If download or hash verification fails.
        """
        latest_release = game_mod.get_latest_release()
        if latest_release is None:
            console.warning(f"No releases found for mod '{game_mod.name}'. Skipping download.")
            return None

        file_path = self.downloader.download_mod(game_mod.name, latest_release.version)

        # Verify integrity using SHA-1
        downloaded_sha1 = FileHasher.calculate_sha1(file_path)
        if downloaded_sha1 != latest_release.sha1:
            console.error(f"Hash mismatch for {game_mod.name} v{latest_release.version}")
            raise DownloadError(f"SHA-1 hash does not match for {game_mod.name}.")

        console.success(f"{game_mod.name} v{latest_release.version} downloaded and verified successfully.")
        return file_path

    def download_latest_releases(self, game_mods: List[GameMod], ignore_list: List[str] = None):
        """
        Downloads the latest release for each mod in the provided list, excluding mods in the ignore list.

        Args:
            game_mods (List[GameMod]): List of GameMod instances to download.
            ignore_list (List[str]): List of mod names to skip.
        """
        ignore_set = set(ignore_list or [])
        mods_to_download = [mod for mod in game_mods if mod.name not in ignore_set]

        console.info(f"Starting download for {len(mods_to_download)} mods.")

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.download_latest_release, mod): mod.name
                for mod in mods_to_download
            }

            for future in as_completed(futures):
                mod_name = futures[future]
                try:
                    future.result()
                    console.success(f"Successfully downloaded {mod_name}")
                except DownloadError as exc:
                    console.error(f"Failed to download {mod_name}: {exc}")

    def download_specific_release(self, game_mod: GameMod, release: Release):
        """
        Downloads a specific release of a mod and verifies its integrity.

        Args:
            game_mod (GameMod): The mod to download.
            release (Release): The release version to download.

        Returns:
            str: The file path of the downloaded mod.

        Raises:
            DownloadError: If download or hash verification fails.
        """
        file_path = self.downloader.download_mod(game_mod.name, release.version)

        downloaded_sha1 = FileHasher.calculate_sha1(file_path)
        if downloaded_sha1 != release.sha1:
            console.error(f"Hash mismatch for {game_mod.name} v{release.version}")
            raise DownloadError(f"SHA-1 hash mismatch for {game_mod.name} v{release.version}")

        console.success(f"{game_mod.name} v{release.version} downloaded and verified successfully.")
        return file_path
