from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from packaging import version
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.changelog import ChangelogEntry


@dataclass
class Image:
    id: str
    thumbnail: str
    url: str


@dataclass
class License:
    description: str
    id: str
    name: str
    title: str
    url: str


@dataclass
class ReleaseInfoJson:
    dependencies: List[str]
    factorio_version: str


@dataclass
class Release:
    download_url: Optional[str] = None
    file_name: str = ""
    info_json: Optional[ReleaseInfoJson] = None
    released_at: Optional[datetime] = None
    sha1: str = ""
    version: str = ""


@dataclass
class GameMod:
    name: str
    category: Optional[str] = None
    changelog: List[ChangelogEntry] = field(default_factory=list)
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    downloads_count: Optional[int] = None
    homepage: Optional[str] = None
    images: List[Image] = field(default_factory=list)
    last_highlighted_at: Optional[datetime] = None
    license: Optional[License] = None
    owner: Optional[str] = None
    releases: List[Release] = field(default_factory=list)
    score: Optional[float] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_json(data: dict) -> 'GameMod':
        def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None

        return GameMod(
            name=data['name'],
            category=data.get('category'),
            changelog=ChangelogEntry.from_changelog_file(data.get('changelog', '')),
            created_at=parse_datetime(data.get('created_at')),
            description=data.get('description'),
            downloads_count=data.get('downloads_count'),
            homepage=data.get('homepage'),
            images=[Image(**img) for img in data.get('images', [])],
            last_highlighted_at=parse_datetime(data.get('last_highlighted_at')),
            license=License(**data['license']) if data.get('license') else None,
            owner=data.get('owner'),
            releases=[
                Release(
                    download_url=release['download_url'],
                    file_name=release['file_name'],
                    info_json=ReleaseInfoJson(**release['info_json']),
                    released_at=parse_datetime(release['released_at']),
                    sha1=release['sha1'],
                    version=release['version']
                ) for release in data.get('releases', [])
            ],
            score=data.get('score'),
            summary=data.get('summary'),
            tags=data.get('tags', []),
            thumbnail=data.get('thumbnail'),
            title=data.get('title'),
            updated_at=parse_datetime(data.get('updated_at'))
        )

    def add_release(self, release: Release) -> None:
        """
        Adds a new Release to the GameMod object.

        Args:
            release (Release): New release
        """
        self.releases.append(release)

    def get_latest_release(self) -> Optional[Release]:
        """
        Returns the release with the highest version. If multiple releases have the same version,
        selects the one with the latest release date (if available).

        Returns:
            Optional[Release]: The latest release based on version and release date.
        """
        sorted_releases = sorted(
            self.releases,
            key=lambda r: (version.parse(r.version), r.released_at or datetime.min),
            reverse=True
        )
        return sorted_releases[0] if sorted_releases else None

    def find_release_by_sha1(self, sha1: str) -> Optional[str]:
        """
        Finds the release version number by the given sha1 hash.

        Args:
            sha1 (str): The sha1 hash of the release file.

        Returns:
            Optional[str]: The version number of the release with the matching sha1 hash, or None if not found.
        """
        for release in self.releases:
            if release.sha1 == sha1:
                return release.version
        return None

    def compare_with_remote(self, remote_mod: 'GameMod') -> Optional['GameMod']:
        """
        Compares the current mod's releases with those from the remote mod.
        Filters releases in the remote mod, retaining only newer ones than the latest installed release.

        Args:
            remote_mod (GameMod): The remote mod instance containing latest release data.

        Returns:
            Optional[GameMod]: The original remote_mod with newer releases or None if no newer releases are found.
        """
        latest_local_release = self.get_latest_release()

        remote_mod.releases = [
            release for release in remote_mod.releases
            if (latest_local_release is None or version.parse(release.version) > version.parse(
                latest_local_release.version))
        ]

        return remote_mod if remote_mod.releases else None

    @staticmethod
    def sync_mod_list_with_remote(local_mods: List['GameMod']) -> List['GameMod']:
        """
        Synchronizes a list of locally installed mods with the latest versions available remotely.
        Checks each mod for newer releases in a multithreaded way, and returns a list of mods
        with only newer releases available.

        Args:
            local_mods (List[GameMod]): List of locally installed mods.

        Returns:
            List[GameMod]: List of mods with updated release information.
        """
        from web_api.factorio_web_api import get_mod_from_web

        updated_mods = []

        with ThreadPoolExecutor() as executor:
            future_to_mod = {executor.submit(get_mod_from_web, mod): mod for mod in local_mods}

            for future in as_completed(future_to_mod):
                local_mod = future_to_mod[future]
                try:
                    remote_mod = future.result()
                    if remote_mod:
                        updated_mod = local_mod.compare_with_remote(remote_mod)
                        if updated_mod:
                            updated_mods.append(updated_mod)
                except Exception as e:
                    print(f"Error syncing mod '{local_mod.name}': {e}")

        return updated_mods