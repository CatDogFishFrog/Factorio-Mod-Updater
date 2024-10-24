import os
import random
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich import print

# Setup console
console = Console()


def _download_mod(name: str, version: str, download_dir: str = "temp") -> str:
    """
    Downloads a mod from the specified URL.

    Args:
        name (str): Name of the mod.
        version (str): Version of the mod.
        download_dir (str): Directory to save the file.

    Returns:
        str: Path to the downloaded file.

    Raises:
        ValueError: If the mod name or version is not provided.
        Exception: If the download fails after two attempts.
    """
    if not name or not version:
        raise ValueError("[red]Mod name and version must be provided.[/red]")

    if not os.path.isdir(download_dir):
        raise ValueError(f"[red]Invalid path: {download_dir}[/red]")

    def try_download_mod():
        download_link = f"https://mods-storage.re146.dev/{name}/{version}.zip?anticache={random.randint(1, 1000000000)}"

        try:
            # Log the start of the download in yellow

            response = requests.get(download_link, stream=True, timeout=10)
            response.raise_for_status()

            file_path = os.path.join(download_dir, f"{name}_{version}.zip")
            total_size = int(response.headers.get('content-length', 0))
            console.print(f"[yellow]Starting download for {name} ({version}): {total_size / (1024 * 1024):.2f} MB[/yellow]")

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            if os.path.getsize(file_path) == 0:
                raise Exception("Downloaded file is empty.")

            # Log success in green
            console.print(f"[green]Mod {name} (version: {version}) successfully downloaded to {file_path}[/green]")
            return file_path

        except (HTTPError, ConnectionError, Timeout) as network_err:
            raise Exception(f"[red]Network error during download: {network_err}[/red]")
        except Exception as err:
            raise Exception(f"[red]General error: {err}[/red]")

    try:
        return try_download_mod()
    except Exception as first_attempt_error:
        console.print(f"[red]Error during the first attempt for {name}: {first_attempt_error}[/red]")
        console.print(f"[yellow]Retrying download for {name}...[/yellow]")
        try:
            return try_download_mod()
        except Exception as second_attempt_error:
            raise Exception(f"[red]Failed to download {name} after two attempts: {second_attempt_error}[/red]")


def download_mods(mod_list: list, download_dir: str = "temp"):
    """
    Downloads multiple mods in parallel, with colored console output.

    Args:
        mod_list (list): List of tuples (mod_name, mod_version).
        download_dir (str): Directory to save the mods.

    Raises:
        Exception: If any download fails after two attempts.
    """
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        future_to_mod = {}

        for mod_name, mod_version in mod_list:
            future = executor.submit(_download_mod, mod_name, mod_version, download_dir)
            future_to_mod[future] = mod_name

        for future in as_completed(future_to_mod):
            mod_name = future_to_mod[future]
            try:
                future.result()  # Raises any exception encountered during the download
            except Exception as exc:
                console.print(f"[red]Failed to download {mod_name}: {exc}[/red]")
