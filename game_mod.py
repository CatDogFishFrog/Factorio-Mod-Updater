import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from packaging import version


def clean_line(line: str) -> str:
    """Cleans a line by removing leading dashes and unnecessary spaces."""
    return re.sub(r'^\s*-\s*', '', line).strip()


def parse_version_block(block: tuple) -> Dict[str, Any]:
    """Parses a single version block into a dictionary."""
    _, date, changes = block
    change_lines = changes.strip().split("\n")
    change_dict = {}
    current_section = None

    for line in change_lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[A-Za-z ]+:", line):  # Detect section headers like "Info:"
            current_section = line[:-1]  # Забираємо двокрапку
            change_dict[current_section] = []
        elif current_section:
            change_dict[current_section].append(clean_line(line))

    return {
        "date": date.strip(),
        "changes": change_dict
    }


def parse_changelog_content(changelog_content: str) -> List[Dict[str, Any]]:
    """
    Parses the given changelog content and returns its content as a list of dictionaries.

    Args:
        changelog_content (str): The full content of the changelog file as a string.

    Returns:
        List[Dict[str, Any]]: Parsed changelog content.
    """
    version_blocks = re.findall(r"Version:\s([0-9.]+)\nDate:\s(.+)\n((?:.|\n)*?)\n-{10,}", changelog_content,
                                re.MULTILINE)

    return [parse_version_block(block) for block in version_blocks]


@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: Dict[str, List[str]]


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
    def parse_changelog(changelog_str: str) -> List[ChangelogEntry]:
        """Parses the changelog string into a list of ChangelogEntry."""
        parsed_changelog = parse_changelog_content(changelog_str)
        return [ChangelogEntry(version=block['date'], date=block['date'], changes=block['changes']) for block in
                parsed_changelog]


    @staticmethod
    def from_json(data: dict) -> 'GameMod':
        def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None

        return GameMod(
            name=data['name'],
            category=data.get('category'),
            changelog=GameMod.parse_changelog(data.get('changelog', '')),
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
        # Спочатку сортуємо за версією, а потім за датою, якщо вона є
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