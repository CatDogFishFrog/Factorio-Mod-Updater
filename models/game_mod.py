from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from utils.date_parser import parse_datetime

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
        Returns the release with the latest release date (if available).

        Returns:
            Optional[Release]: The latest release based on release date.
        """
        if not self.releases:
            return None
        # Sort releases by release date, descending
        latest_release = max(self.releases, key=lambda r: r.released_at or datetime.min)
        return latest_release

    def find_release_by_sha1(self, sha1: str) -> Optional[Release]:
        """
        Finds the release version number by the given sha1 hash.

        Args:
            sha1 (str): The sha1 hash of the release file.

        Returns:
            Optional[str]: The version number of the release with the matching sha1 hash, or None if not found.
        """
        for release in self.releases:
            if release.sha1 == sha1:
                return release
        return None