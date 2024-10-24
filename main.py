import parse_mod_files
import mod_downloader
import json

import re
import sys

import requests


def fetch_and_parse_json(url):
    """
    Fetches a JSON file from the given URL and parses its content.

    Args:
        url (str): URL of the JSON file to fetch and parse.

    Returns:
        dict: Parsed content of the JSON file.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching JSON from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {url}: {e}")
        return None


def clean_line(line):
    """Cleans a line by removing leading dashes and unnecessary spaces."""
    return re.sub(r'^\s*-\s*', '', line)


def parse_version_block(block):
    """Parses a single version block into a dictionary."""
    _, date, changes = block
    change_lines = changes.strip().split("\n")
    change_dict = {}
    current_section = None

    for line in change_lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[A-Za-z ]+:", line):  # Detect section headers like "Features:"
            current_section = line[:-1]
            change_dict[current_section] = []
        elif current_section:
            change_dict[current_section].append(clean_line(line))

    return {
        "date": date,
        "changes": change_dict
    }


def parse_changelog(changelog_file_path):
    """
    Parses the given changelog.txt file and returns its content as a dictionary.

    Args:
        changelog_file_path (str): Path to the changelog.txt file to parse.

    Returns:
        dict: Parsed changelog content with version, date, and changes.
    """
    changelog_data = {}

    try:
        with open(changelog_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Regular expression to match version blocks
        version_blocks = re.findall(r"Version:\s([0-9.]+)\nDate:\s(.+)\n((?:.|\n)*?)\n-{10,}", content, re.MULTILINE)

        for block in version_blocks:
            version_info = parse_version_block(block)
            changelog_data[block[0]] = version_info

        return changelog_data

    except FileNotFoundError as e:
        raise FileNotFoundError(f"File {changelog_file_path} not found.") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred while parsing changelog: {e}") from e


def main():
    try:
        # mod_list = parse_mod_files.get_mods_list("C:\\Games\\Factorio_2.0.8\\mods")
        # print(mod_list)
        mod_list = [("AutoDeconstruct", "1.0.2"), ("Smart_Inserters", "2.0.6"), ("cargo-ships", "1.0.8"), ("alien-biomes-graphics", "0.7.0"), ("Krastorio2Assets", "1.2.3")]
        mod_downloader.download_mods(mod_list, download_dir="temp")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()