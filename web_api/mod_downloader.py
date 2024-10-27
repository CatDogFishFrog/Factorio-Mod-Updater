import os
import random
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from concurrent.futures import ThreadPoolExecutor, as_completed

from exceptions.exceptions import DownloadError, EmptyFileError
from models.game_mod import GameMod
from utils.file_hasher import FileHasher
from utils.singleton_console import ConsoleSingleton

# Console setup
console = ConsoleSingleton()

class ModValidator:
    @staticmethod
    def validate(name: str, version: str, download_dir: str):
        """Validate the inputs for the mod download."""
        if not name or not version:
            raise ValueError("Mod name and version must be provided.")
        if not os.path.isdir(download_dir):
            raise ValueError(f"Invalid path: {download_dir}")


class ModDownloader:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)




    def download_mod(self, name: str, version: str) -> str:
        """Initiate download and handle retries."""
        ModValidator.validate(name, version, self.download_dir)
        download_link = self._generate_download_link(name, version)
        file_path = os.path.join(self.download_dir, f"{name}_{version}.zip")

        try:
            return self._download_with_retry(download_link, file_path)
        except DownloadError as e:
            console.print_error(f"Download failed for {name}: {e}")
            raise

    def _generate_download_link(self, name: str, version: str) -> str:
        """Generate a download link with anti-cache parameter."""
        anticache = random.randint(1, 1_000_000_000)
        return f"https://mods-storage.re146.dev/{name}/{version}.zip?anticache={anticache}"

    def _download_with_retry(self, download_link: str, file_path: str) -> str:
        """Attempt download with a retry mechanism."""
        try:
            return self._download_from_url(download_link, file_path)
        except DownloadError as e:
            console.print_warning(f"Retrying download for: {file_path} due to: {e}")
            return self._download_from_url(download_link, file_path)

    def _download_from_url(self, download_link: str, file_path: str) -> str:
        """Perform actual download and check for empty file."""
        try:
            response = requests.get(download_link, stream=True, timeout=10)
            response.raise_for_status()
            self._save_file(response, file_path)
            if os.path.getsize(file_path) == 0:
                raise EmptyFileError("Downloaded file is empty.")
            return file_path
        except (HTTPError, ConnectionError, Timeout) as e:
            raise DownloadError(f"Network error during download: {e}")

    def _save_file(self, response, file_path: str):
        """Save downloaded content to the file."""
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)


class ModDownloadManager:
    def __init__(self, download_dir: str = "temp"):
        self.download_dir = download_dir
        self.downloader = ModDownloader(download_dir)

    def downloqd_latest_release(self, game_mod: GameMod):
        lstest_release = game_mod.get_latest_release()
        self.downloader.download_mod(game_mod.name, lstest_release.version)

        if FileHasher.calculate_sha1(os.path.join(self.download_dir, lstest_release.file_name)) != lstest_release.sha1:
            raise DownloadError("Downloaded file hash does not match the expected SHA-1 hash.")



    def download_mods(self, mod_list: list):
        """Download multiple mods concurrently with error handling."""
        with ThreadPoolExecutor() as executor:
            future_to_mod = {executor.submit(self.downloader.download_mod, name, version): name
                             for name, version in mod_list}
            for future in as_completed(future_to_mod):
                mod_name = future_to_mod[future]
                try:
                    future.result()
                    console.print_success(f"Successfully downloaded {mod_name}")
                except DownloadError as exc:
                    console.print_error(f"Failed to download {mod_name}: {exc}")
