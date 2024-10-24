import os
import random
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

# Setup console
console = Console()


class DownloadError(Exception):
    pass


class EmptyFileError(Exception):
    pass


def _validate_mod_inputs(name: str, version: str, download_dir: str):
    """Validate the inputs for the mod download."""
    if not name or not version:
        raise ValueError("[red]Mod name and version must be provided.[/red]")
    if not os.path.isdir(download_dir):
        raise ValueError(f"[red]Invalid path: {download_dir}[/red]")


def _download_from_url(download_link: str, file_path: str):
    """Download the file from the URL."""
    try:
        response = requests.get(download_link, stream=True, timeout=10)
        response.raise_for_status()

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        if os.path.getsize(file_path) == 0:
            raise EmptyFileError("Downloaded file is empty.")

        return file_path

    except (HTTPError, ConnectionError, Timeout) as network_err:
        raise DownloadError(f"Network error during download: {network_err}")
    except EmptyFileError as e:
        raise e
    except Exception as err:
        raise DownloadError(f"General error: {err}")


def _download_mod(name: str, version: str, download_dir: str = "temp") -> str:
    """Download a mod from the specified URL."""
    _validate_mod_inputs(name, version, download_dir)

    download_link = f"https://mods-storage.re146.dev/{name}/{version}.zip?anticache={random.randint(1, 1000000000)}"
    file_path = os.path.join(download_dir, f"{name}_{version}.zip")
    console.print(f"[yellow]Starting download for {name} ({version})...[/yellow]")

    try:
        return _download_from_url(download_link, file_path)
    except Exception as first_attempt_error:
        console.print(f"[red]Error during the first attempt for {name}: {first_attempt_error}[/red]")
        console.print(f"[yellow]Retrying download for {name}...[/yellow]")
        try:
            return _download_from_url(download_link, file_path)
        except Exception as second_attempt_error:
            raise DownloadError(f"[red]Failed to download {name} after two attempts: {second_attempt_error}[/red]")


def download_mods(mod_list: list, download_dir: str = "temp"):
    """Download multiple mods in parallel, with colored console output."""
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        future_to_mod = {executor.submit(_download_mod, mod_name, mod_version, download_dir): mod_name for
                         mod_name, mod_version in mod_list}

        for future in as_completed(future_to_mod):
            mod_name = future_to_mod[future]
            try:
                future.result()  # Raises any exception encountered during the download
            except Exception as exc:
                console.print(f"[red]Failed to download {mod_name}: {exc}[/red]")
