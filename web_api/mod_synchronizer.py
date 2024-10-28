from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from packaging import version

from models.game_mod import GameMod
from web_api.factorio_web_api import FactorioAPIClient
from utils.singleton_console import ConsoleSingleton

console = ConsoleSingleton()

class ModSynchronizer:
    def __init__(self, api_client: FactorioAPIClient):
        """
        Initializes ModSynchronizer with an API client to fetch remote mod data.

        Args:
            api_client (FactorioAPIClient): An instance of FactorioAPIClient to retrieve mod data from remote API.
        """
        self.api_client = api_client

    @staticmethod
    def find_new_releases_from_remote(local_mod: GameMod, remote_mod: GameMod) -> Optional[GameMod]:
        """
        Compares releases between a local mod and its remote counterpart, retaining only newer releases.

        Args:
            local_mod (GameMod): The local mod instance with current release information.
            remote_mod (GameMod): The remote mod instance with up-to-date release data.

        Returns:
            Optional[GameMod]: Updated remote_mod with filtered releases if newer versions are available,
            otherwise None if no updates are found.
        """
        latest_local_release = local_mod.get_latest_release()

        # Filter only newer releases than the local latest release
        remote_mod.releases = [
            release for release in remote_mod.releases
            if latest_local_release is None or version.parse(release.version) > version.parse(latest_local_release.version)
        ]

        return remote_mod if remote_mod.releases else None

    def find_updates_of_mods_list(self, local_mods: List[GameMod]) -> List[GameMod]:
        """
        Synchronizes a list of locally installed mods with the latest versions available remotely.
        Uses multithreading to check each mod for newer releases concurrently.

        Args:
            local_mods (List[GameMod]): List of locally installed mods.

        Returns:
            List[GameMod]: List of mods with newer releases available.
        """
        updated_mods = []

        with ThreadPoolExecutor() as executor:
            # Submit tasks to fetch mod details concurrently
            future_to_mod = {executor.submit(self.api_client.get_mod_details, mod): mod for mod in local_mods}

            for future in as_completed(future_to_mod):
                local_mod = future_to_mod[future]
                try:
                    # Get remote mod details
                    remote_mod = future.result()
                    if remote_mod:
                        # Compare and update if newer releases exist
                        updated_mod = self.find_new_releases_from_remote(local_mod, remote_mod)
                        if updated_mod:
                            updated_mods.append(updated_mod)
                            console.success(f"Updates found for mod '{local_mod.name}'")
                except Exception as e:
                    console.error(f"Error syncing mod '{local_mod.name}': {e}")

        return updated_mods