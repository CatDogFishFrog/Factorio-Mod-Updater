import json
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


# def get_mod_info_from_web(modlist:list):
#     web_mod_list = []
#     for
#     fetch_and_parse_json()