import re
from dataclasses import dataclass
from typing import List

@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: str


def split_changelog(changelog_content: str) -> List[str]:
    """Splits the changelog content into blocks based on dash separators (variable length)."""
    return re.split(r"-{10,}", changelog_content)


def parse_version_block(blocks) -> ChangelogEntry | None:
    """Parses a single version block into a dictionary."""

    regex_pattern = r"Version:\s*([0-9.]+)\s*\n\Date:\s*(.*?)\s*\n {2}([\s\S]*)"

    match = re.search(regex_pattern, blocks, re.MULTILINE)
    if not match:
        return None
    version, date, changes = match.groups()

    return ChangelogEntry(
        version=version,
        date=date,
        changes=changes
    )


def parse_changelog(changelog_str: str) -> List[ChangelogEntry]:
    """Parses the changelog string into a list of ChangelogEntry."""
    parsed_changelog = split_changelog(changelog_str)
    return [parse_version_block(block) for block in parsed_changelog if block]

