import json
import requests
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.game_mod import GameMod
from utils.singleton_console import ConsoleSingleton

console = ConsoleSingleton()

def get_mod_from_web(game_mod: GameMod) -> Optional[GameMod]:
    """
    Fetches detailed information about a single mod from the Factorio web API
    and creates a GameMod instance from the received JSON data.

    Args:
        game_mod (GameMod): An instance representing the mod with basic details (e.g., name).

    Returns:
        Optional[GameMod]: A GameMod instance populated with additional data from the API, or None if an error occurred.
    """
    url = f"https://mods.factorio.com/api/mods/{game_mod.name}/full"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for HTTP errors (4xx and 5xx)
        return GameMod.from_json(response.json())
    except requests.exceptions.HTTPError as e:
        console.print_error(f"HTTP error while fetching JSON from {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        console.print_error(f"Connection error while accessing {url}: {e}")
    except requests.exceptions.Timeout as e:
        console.print_error(f"Request timed out while accessing {url}: {e}")
    except requests.exceptions.RequestException as e:
        console.print_error(f"Unexpected error with the request to {url}: {e}")
    except json.JSONDecodeError as e:
        console.print_error(f"Error decoding JSON from {url}: {e}")
    return None

def get_mods_from_web(game_mods: List[GameMod]) -> List[Optional[GameMod]]:
    """
    Fetches detailed information for multiple mods from the Factorio web API using multithreading.

    Args:
        game_mods (List[GameMod]): A list of GameMod instances with basic information (e.g., names).

    Returns:
        List[Optional[GameMod]]: A list of GameMod instances populated with data from the API. Returns None for any mod that caused an error.
    """
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_mod = {executor.submit(get_mod_from_web, mod): mod for mod in game_mods}
        for future in as_completed(future_to_mod):
            mod = future_to_mod[future]
            try:
                mod_data = future.result()
                results.append(mod_data)
            except Exception as e:
                console.print_error(f"Error occurred while processing mod '{mod.name}': {e}")
                results.append(None)
    return results