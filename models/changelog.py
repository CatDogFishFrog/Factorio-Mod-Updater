import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: str

    @staticmethod
    def split_changelog(changelog_content: str) -> List[str]:
        """Splits the changelog content into blocks based on dash separators (variable length)."""
        return re.split(r"-{10,}", changelog_content.strip())

    @staticmethod
    def from_version_block(block: str) -> Optional["ChangelogEntry"]:
        """Parses a single version block into a ChangelogEntry."""
        regex_pattern = r"Version:\s*([0-9.]+)\s*\n\s*Date:\s*(.*?)\s*\n([\s\S]*)"
        match = re.search(regex_pattern, block.strip(), re.MULTILINE)
        if not match:
            return None
        version, date, changes = match.groups()
        return ChangelogEntry(version=version.strip(), date=date.strip(), changes=changes.strip())

    @classmethod
    def from_changelog_file(cls, changelog_str: str) -> List["ChangelogEntry"]:
        """Parses the changelog string into a list of ChangelogEntry."""
        parsed_changelog = cls.split_changelog(changelog_str)
        return [entry for block in parsed_changelog if (entry := cls.from_version_block(block))]
