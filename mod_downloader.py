import os
import random
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn


def _download_mod(name: str, version: str, download_dir: str = "temp", task_id: int = None,
                  progress: Progress = None) -> str:
    """
    Downloads a mod from the specified URL.

    Args:
        name (str): Name of the mod.
        version (str): Version of the mod.
        download_dir (str): Directory to save the file.
        task_id (int, optional): Task ID for the progress bar.
        progress (rich.progress.Progress, optional): Progress bar object.

    Returns:
        str: Path to the downloaded file.

    Raises:
        ValueError: If the mod name or version is not provided.
        Exception: If the download fails after two attempts.
    """
    if not name or not version:
        raise ValueError("Mod name and version must be provided.")

    if not os.path.isdir(download_dir):
        raise ValueError(f"Invalid path: {download_dir}")

    def try_download_mod():
        download_link = f"https://mods-storage.re146.dev/{name}/{version}.zip?anticache={random.randint(1, 1000000000)}"
        print(f"Attempting to download mod from: {download_link}")

        try:
            response = requests.get(download_link, stream=True, timeout=10)
            response.raise_for_status()

            file_path = os.path.join(download_dir, f"{name}_{version}.zip")
            total_size = int(response.headers.get('content-length', 0))

            if progress and task_id:
                progress.update(task_id, total=total_size)

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        if progress and task_id:
                            progress.update(task_id, advance=len(chunk))

            if os.path.getsize(file_path) == 0:
                raise Exception("Downloaded file is empty.")

            print(f"Mod successfully downloaded to: {file_path}")
            return file_path

        except (HTTPError, ConnectionError, Timeout) as network_err:
            raise Exception(f"Network error during download: {network_err}")
        except Exception as err:
            raise Exception(f"General error: {err}")

    try:
        return try_download_mod()
    except Exception as first_attempt_error:
        print(f"Error during the first attempt: {first_attempt_error}")
        print("Retrying download...")
        if progress and task_id:
            progress.reset(task_id)
        try:
            return try_download_mod()
        except Exception as second_attempt_error:
            raise Exception(f"Failed to download mod after two attempts: {second_attempt_error}")


def download_mods(mod_list: list, download_dir: str = "temp"):
    """
    Downloads multiple mods in parallel, with progress bars for each download.

    Args:
        mod_list (list): List of tuples (mod_name, mod_version).
        download_dir (str): Directory to save the mods.

    Raises:
        Exception: If any download fails after two attempts.
    """
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    with Progress(
            TextColumn("[bold blue]{task.fields[mod_name]}:[/bold blue]"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
    ) as progress:
        with ThreadPoolExecutor() as executor:
            tasks = {}
            future_to_mod = {}

            for mod_name, mod_version in mod_list:
                task_id = progress.add_task(f"Downloading {mod_name}", mod_name=mod_name, total=0)
                future = executor.submit(_download_mod, mod_name, mod_version, download_dir, task_id, progress)
                future_to_mod[future] = mod_name
                tasks[mod_name] = task_id

            for future in as_completed(future_to_mod):
                mod_name = future_to_mod[future]
                try:
                    future.result()  # Raises any exception encountered during the download
                except Exception as exc:
                    print(f"Failed to download {mod_name}: {exc}")
                finally:
                    progress.remove_task(tasks[mod_name])
